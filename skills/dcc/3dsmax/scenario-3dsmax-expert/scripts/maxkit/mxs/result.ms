-- maxkit/mxs/result.ms: JSON text from MAXScript values (twin of maxkit/result.py)
-- Checked against scripting-pipeline__3dsmaxbatch-2020.md
-- (Dictionary keys, GetDictValue) and scripting-pipeline__maxscript-file-loading-saving-importfile-exportfile-2027.md.
-- Inlined by max_wrap inside one outer block, so every fn below is local to that block.
-- Uses no blocked command (no dotNet, no python, no file delete or copy, no INI write).

fn mxk_jsonStr s = (
    local t = s as string
    t = substituteString t "\\" "\\\\"  -- [verify] substituteString
    t = substituteString t "\"" "\\\""
    t = substituteString t "\n" "\\n"
    t = substituteString t "\r" "\\r"
    t = substituteString t "\t" "\\t"
    "\"" + t + "\""
)

fn mxk_toJson v = (  -- [verify] recursion of a block-local fn
    local c = classOf v
    case of (
        (v == undefined): "null"
        (c == BooleanClass): (if v then "true" else "false")  -- [verify] BooleanClass
        (c == Integer or c == Float or c == Double or c == Integer64): (  -- [verify] Double, Integer64
            if c == Float or c == Double then (formattedPrint v format:".6g") else (v as string)  -- [verify] formattedPrint
        )
        (c == String): mxk_jsonStr v
        (c == Name): mxk_jsonStr (v as string)
        (c == Point3): ("[" + (mxk_toJson v.x) + "," + (mxk_toJson v.y) + "," + (mxk_toJson v.z) + "]")
        (c == Point2): ("[" + (mxk_toJson v.x) + "," + (mxk_toJson v.y) + "]")
        (c == Color): ("[" + (mxk_toJson v.r) + "," + (mxk_toJson v.g) + "," + (mxk_toJson v.b) + "]")
        (c == Array): (
            local parts = for x in v collect (mxk_toJson x)
            local s = "["
            for i = 1 to parts.count do s += (if i > 1 then "," else "") + parts[i]
            s + "]"
        )
        (c == Dictionary): (  -- [verify] Dictionary class name
            local s = "{"
            local first = true
            for k in v.keys do (
                s += (if first then "" else ",") + (mxk_jsonStr (k as string)) + ":" + (mxk_toJson (GetDictValue v k))
                first = false
            )
            s + "}"
        )
        (isValidNode v): mxk_jsonStr v.name  -- [verify] isValidNode
        default: mxk_jsonStr (v as string)
    )
)

fn mxk_dict pairs = (
    -- pairs: #(#(key, value), ...) -> Dictionary with string keys
    local d = Dictionary #string  -- [verify] Dictionary #string constructor
    for p in pairs do PutDictValue d (p[1] as string) p[2]  -- [verify] PutDictValue
    d
)
