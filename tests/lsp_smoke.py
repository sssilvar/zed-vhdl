"""Exercise a real VHDL LS process with bounded LSP requests and shutdown."""
from __future__ import annotations

import json
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from typing import Any


def read_messages(pipe: Any, messages: queue.Queue) -> None:
    try:
        while True:
            headers = {}
            while line := pipe.readline():
                if line == b'\r\n':
                    break
                key, value = line.decode().split(':', 1)
                headers[key.lower()] = value.strip()
            if not line:
                return
            length = int(headers['content-length'])
            if length > 8 * 1024 * 1024:
                raise ValueError('oversized LSP message')
            payload = pipe.read(length)
            messages.put(json.loads(payload))
    except Exception as error:
        messages.put(error)


def main() -> None:
    binary = Path(sys.argv[1]).resolve()
    fixture = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else Path(__file__).resolve().parents[1] / 'examples/blinker'
    with tempfile.TemporaryDirectory(prefix='zed-vhdl-lsp-') as temp:
        root = Path(temp)
        for source in fixture.rglob('*'):
            if source.is_file() and (source.suffix == '.vhd' or source.name == 'vhdl_ls.toml'):
                destination = root / source.relative_to(fixture)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
        document = next(root.rglob('blinker.vhd'))
        text = document.read_text()
        uri = document.as_uri()
        with (root / 'stderr.log').open('wb') as errors:
            process = subprocess.Popen([str(binary)], cwd=root, stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, stderr=errors)
            messages: queue.Queue = queue.Queue(maxsize=256)
            threading.Thread(target=read_messages, args=(process.stdout, messages), daemon=True).start()
            request_id = 0

            def send(method: str, params: Any, identifier: int | None = None) -> None:
                message = {'jsonrpc': '2.0', 'method': method, 'params': params}
                if identifier is not None:
                    message['id'] = identifier
                data = json.dumps(message).encode()
                process.stdin.write(f'Content-Length: {len(data)}\r\n\r\n'.encode() + data)
                process.stdin.flush()

            def receive(predicate: Any) -> dict:
                import time
                deadline = time.monotonic() + 15
                while True:
                    message = messages.get(timeout=max(0.01, deadline - time.monotonic()))
                    if isinstance(message, Exception):
                        raise message
                    if message.get('method') in ('window/showMessage', 'window/logMessage'):
                        notice = message['params']
                        if notice.get('type', 4) <= 2:
                            raise RuntimeError(f"Language server reported: {notice['message']}")
                    if 'method' in message and 'id' in message:
                        reply = json.dumps({'jsonrpc': '2.0', 'id': message['id'], 'result': None}).encode()
                        process.stdin.write(f'Content-Length: {len(reply)}\r\n\r\n'.encode() + reply)
                        process.stdin.flush()
                    if predicate(message):
                        return message
                    if time.monotonic() >= deadline:
                        raise TimeoutError('LSP response deadline exceeded')

            def request(method: str, params: Any) -> Any:
                nonlocal request_id
                request_id += 1
                send(method, params, request_id)
                response = receive(lambda message: message.get('id') == request_id)
                if 'error' in response:
                    raise RuntimeError(response['error'])
                return response['result']

            try:
                result = request('initialize', {'processId': None, 'rootUri': root.as_uri(),
                                 'capabilities': {'textDocument': {'completion': {'completionItem': {'snippetSupport': True}}}}})
                capabilities = result['capabilities']
                for feature in ('hoverProvider', 'definitionProvider', 'completionProvider', 'renameProvider'):
                    assert capabilities.get(feature), feature
                send('initialized', {})
                send('textDocument/didOpen', {'textDocument': {'uri': uri, 'languageId': 'vhdl', 'version': 1, 'text': text}})
                line = next(i for i, line in enumerate(text.splitlines()) if 'counter <= counter' in line)
                position = {'textDocument': {'uri': uri}, 'position': {'line': line, 'character': 8}}
                assert request('textDocument/hover', position), 'hover'
                assert request('textDocument/definition', position), 'definition'
                completion = request('textDocument/completion', position)
                items = completion if isinstance(completion, list) else completion['items']
                assert any(item['label'] == 'counter' for item in items), items
                rename = request('textDocument/rename', {**position, 'newName': 'count'})
                assert rename and (rename.get('changes') or rename.get('documentChanges')), rename
                assert request('textDocument/documentSymbol', {'textDocument': {'uri': uri}}), 'symbols'
                send('textDocument/didChange', {'textDocument': {'uri': uri, 'version': 2}, 'contentChanges': [{'text': text.replace('counter + 1', 'missing + 1')}]})
                diagnostic = receive(lambda message: message.get('method') == 'textDocument/publishDiagnostics' and message['params']['uri'] == uri and any(d.get('severity') == 1 for d in message['params']['diagnostics']))
                assert diagnostic['params']['diagnostics']
                send('textDocument/didChange', {'textDocument': {'uri': uri, 'version': 3}, 'contentChanges': [{'text': text}]})
                diagnostic = receive(lambda message: message.get('method') == 'textDocument/publishDiagnostics' and message['params']['uri'] == uri and not message['params']['diagnostics'])
                for testbench in root.rglob('tb_blinker.vhd'):
                    bench = testbench.read_text()
                    bench_uri = testbench.as_uri()
                    send('textDocument/didOpen', {'textDocument': {'uri': bench_uri, 'languageId': 'vhdl', 'version': 1, 'text': bench}})
                    finish_line = next(i for i, line in enumerate(bench.splitlines()) if line.strip() == 'finish;')
                    assert request('textDocument/definition', {'textDocument': {'uri': bench_uri}, 'position': {'line': finish_line, 'character': 5}}), 'std.env.finish definition'
                request('shutdown', None)
                send('exit', None)
                process.wait(timeout=5)
                assert process.returncode == 0, process.returncode
                print('PASS: initialization, IEEE libraries, completion, hover, definition, rename, symbols, live diagnostics and shutdown')
            finally:
                errors.flush()
                log = (root / 'stderr.log').read_text()
                if log:
                    print(log, file=sys.stderr)
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=5)


if __name__ == '__main__':
    main()
