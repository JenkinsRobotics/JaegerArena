// Presentation-only example records. This site never executes an agent or training job.
document.documentElement.classList.remove('no-js');
const steps = [
  {
    kicker: '01 / Set the conditions',
    title: 'Give the challenge a clear finish line.',
    body: 'Choose a task, freeze its rubric, and define the allowed tools and budget. Comparable results begin with comparable conditions.',
    example: 'Repair a failing parser',
    records: [['Challenge', 'Parser repair · revision 1'], ['Evaluation', 'Correctness + regression checks'], ['Conditions', 'Fixed tools and runtime budget']],
  },
  {
    kicker: '02 / Capture the attempt',
    title: 'Keep the work behind the result.',
    body: 'Run through an execution adapter. Record the participant, configuration, outputs, errors, and resource use so the attempt can be understood later.',
    example: 'A baseline with a trace',
    records: [['Participant', 'Example agent · configuration A'], ['Artifacts', 'Patch, test output, and tool trace'], ['Outcome', 'Parser still fails on empty input']],
  },
  {
    kicker: '03 / Evaluate independently',
    title: 'Turn an outcome into useful feedback.',
    body: 'Apply the fixed rubric and preserve the evidence behind each finding. The participant cannot rewrite the grader to improve its own score.',
    example: 'The missing edge case',
    records: [['Finding', 'Empty input is not handled'], ['Evidence', 'Failing test + parser output'], ['Decision', 'Practice needed; no promotion']],
  },
  {
    kicker: '04 / Build a candidate',
    title: 'Record exactly what training changed.',
    body: 'Use feedback to revise a skill or invoke a training backend. Track skill, prompt, memory, and model updates as distinct change types.',
    example: 'A revised parsing skill',
    records: [['Change type', 'Skill revision; model unchanged'], ['Practice', 'Input validation exercises'], ['Candidate', 'Configuration B, linked to A']],
  },
  {
    kicker: '05 / Test beyond practice',
    title: 'Prove the candidate on reserved tasks.',
    body: 'Assess the candidate against tasks kept separate from training. Compare it with the baseline and check for regressions before accepting a change.',
    example: 'Independent assessment',
    records: [['Task set', 'Reserved parser cases'], ['Comparison', 'Baseline A versus candidate B'], ['Gate', 'Repeated passes + no regressions']],
  },
  {
    kicker: '06 / Make an evidence-based decision',
    title: 'Keep the progress. Keep the explanation.',
    body: 'Accept a candidate only when the progression policy is met. Otherwise retain the previous accepted version, record the rejection, and choose the next practice task.',
    example: 'A traceable progression decision',
    records: [['If qualified', 'Accept B and record its evidence'], ['If regressed', 'Keep A; retain the failed attempt'], ['XP vs mastery', 'Practice and capability stay distinct']],
  },
];

const buttons = [...document.querySelectorAll('[data-step]')];
function selectStep(index) {
  const step = steps[index];
  document.querySelector('#step-kicker').textContent = step.kicker;
  document.querySelector('#step-title').textContent = step.title;
  document.querySelector('#step-body').textContent = step.body;
  document.querySelector('#example-title').textContent = step.example;
  step.records.forEach(([label, value], i) => {
    document.querySelector('#record-label-' + (i + 1)).textContent = label;
    document.querySelector('#record-value-' + (i + 1)).textContent = value;
  });
  buttons.forEach((button, i) => button.setAttribute('aria-pressed', String(i === index)));
}
buttons.forEach((button, index) => {
  button.addEventListener('click', () => selectStep(index));
  button.addEventListener('keydown', event => {
    let next;
    if (event.key === 'ArrowRight') next = (index + 1) % buttons.length;
    if (event.key === 'ArrowLeft') next = (index + buttons.length - 1) % buttons.length;
    if (event.key === 'Home') next = 0;
    if (event.key === 'End') next = buttons.length - 1;
    if (next === undefined) return;
    event.preventDefault();
    selectStep(next);
    buttons[next].focus();
  });
});
