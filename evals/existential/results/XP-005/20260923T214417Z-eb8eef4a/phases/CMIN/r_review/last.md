REPAIR:

The candidate does not yet meet the brief: the UI sends no client intent ID, a competing ID can bind to an existing operation, and a retry after uncertain paid acquisition can call `acquire` again.

- Give each consequential client submission a durable identity that survives a lost response and restart. Bind it exclusively to its operation before dispatch. Reject changed payloads and competing or unidentified requests while that operation is unresolved, including concurrent requests.
- Reconcile an uncertain paid acquisition against evidence for the exact provider effect before considering another acquisition. A title-only video match is insufficient to attribute a publish; ambiguous evidence must block further dispatch.
- Return the original operation’s actual outcome and known effect identity on retries, including terminal retries.
- Demonstrate these outcomes with local fixtures for lost responses, restart, competing requests, and ambiguous evidence. No live consequential submissions.