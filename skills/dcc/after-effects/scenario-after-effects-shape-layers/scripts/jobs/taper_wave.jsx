// channel: bridge | handoff
// checked: live 27.0
var S = AEX.shapes, l = AEK.core.layer(AEK.core.comp(ARGS.comp), ARGS.layer), gp = ARGS.group ? [ARGS.group] : [];
var st = S.contents(l, gp).property("ADBE Vector Graphic - Stroke");
S.set(st.property("ADBE Vector Stroke Taper"), { "ADBE Vector Taper Start Length": 64, "ADBE Vector Taper End Length": 36,
  "ADBE Vector Taper Start Width": 25, "ADBE Vector Taper End Width": 0, "ADBE Vector Taper Start Ease": 9, "ADBE Vector Taper End Ease": 59 });
st = S.contents(l, gp).property("ADBE Vector Graphic - Stroke");
S.set(st.property("ADBE Vector Stroke Wave"), { "ADBE Vector Taper Wave Amount": 31, "ADBE Vector Taper Wavelength": 186 });
st = S.contents(l, gp).property("ADBE Vector Graphic - Stroke");
AEK.expr.set(st.property("ADBE Vector Stroke Wave").property("ADBE Vector Taper Wave Phase"), "time * -100", [0, 1]);
return S.dump(S.contents(l, gp).property("ADBE Vector Graphic - Stroke"));
