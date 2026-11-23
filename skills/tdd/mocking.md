# When to Mock

Mock at **system boundaries** only; use real code for everything you control:

- External APIs (payment, email, etc.)
- Databases: use a test DB; mock one only when none can run where the tests run
- Time/randomness
- File system: use a temp directory; mock it only when that is impossible

## Designing for Mockability

At system boundaries, pass external dependencies in (dependency injection), so the test hands over a fake:

```typescript
function processPayment(order, paymentClient) {
  return paymentClient.charge(order.total);
}
```

Prefer SDK-style interfaces over generic fetchers: give each external operation its own function, so each mock returns one specific shape:

```typescript
const api = {
  getUser: (id) => fetch(`/users/${id}`),
  getOrders: (userId) => fetch(`/users/${userId}/orders`),
  createOrder: (data) => fetch('/orders', { method: 'POST', body: data }),
};
```
