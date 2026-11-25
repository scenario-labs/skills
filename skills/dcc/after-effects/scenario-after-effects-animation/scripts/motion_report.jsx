// motion_report.jsx: motion review of one comp. Job for ae.py run, with --lib animation.jsx. It calls AEX.animation.report.
// ARGS: {comp: "Name", props: ["ADBE Position", "ADBE Scale", "ADBE Rotate Z"] (optional), open: "/abs/project.aep" (own test session only)}
// On an After Effects shared by several jobs, call AEX.animation.report(comp) at the end of the job that built the comp instead:
// `open` closes whatever project is open, without saving. Reads only: nothing is added to the comp.
if (ARGS.open) { AEK.core.open(ARGS.open); }
return AEX.animation.report(AEK.core.comp(ARGS.comp), ARGS.props);
