// Replaced in Task 3. The test pool loads the Worker's main entry, so it must exist from Task 1.
export default { async fetch() { return new Response('Not found', { status: 404 }); } };
