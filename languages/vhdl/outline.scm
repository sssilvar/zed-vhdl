(entity_declaration "entity" @context name: (_) @name) @item
(architecture_body "architecture" @context name: (_) @name "of" @context entity: (_) @context) @item
(package_declaration "package" @context name: (_) @name) @item
(package_body "package" @context "body" @context package: (_) @name) @item
(function_body "function" @context designator: (_) @name) @item
(procedure_body "procedure" @context designator: (_) @name) @item
(component_declaration "component" @context name: (_) @name) @item
(full_type_declaration "type" @context name: (_) @name) @item
(process_statement . (label)? @name . "process" @context) @item
