(identifier) @variable
(comment) @comment
(string_literal) @string
(character_literal) @string
(integer_decimal) @number
["library" "use" "entity" "architecture" "of" "is" "begin" "end"
 "port" "generic" "map" "in" "out" "inout" "buffer" "signal"
 "variable" "constant" "type" "subtype" "range" "array" "record"
 "process" "if" "then" "elsif" "else" "case" "when" "others"
 "for" "while" "loop" "generate" "return" "function" "procedure"
 "package" "body" "component" "configuration" "context" "assert"
 "report" "severity" "wait" "until" "after"] @keyword
["and" "or" "xor" "not" "nand" "nor" "xnor" "mod" "rem"
 "sll" "srl" "sla" "sra" "rol" "ror" "=" "/=" "<" ">" "<=" ">="
 "+" "-" "*" "/" "&" ":=" "=>"] @operator
["(" ")" "[" "]"] @punctuation.bracket
[";" ":" "," "."] @punctuation.delimiter
(entity_declaration name: (_) @type)
(architecture_body name: (_) @type entity: (_) @type)
(package_declaration name: (_) @type)
(full_type_declaration name: (_) @type)
(subtype_declaration name: (_) @type)
(function_declaration designator: (_) @function)
(function_body designator: (_) @function)
(procedure_declaration designator: (_) @function)
(procedure_body designator: (_) @function)
(attribute_name) @attribute

(real_decimal) @number
(based_integer) @number
(bit_string_literal) @number
(extended_identifier) @variable
