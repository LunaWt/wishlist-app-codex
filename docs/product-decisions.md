# Product decisions (for submission)

1. **Public link without registration**
   - Anyone can open wishlist by URL.
   - To reserve or contribute, guest creates lightweight guest session (name + token).

2. **Surprise preservation**
   - Owner never sees who reserved or who contributed.
   - Owner only sees aggregate reservation state and funding progress.

3. **Gift modes**
   - `single`: one guest reserves the gift.
   - `group`: multiple guests contribute to target amount.

4. **Contribution policy**
   - Minimum contribution: 1 unit of wishlist currency.
   - If user enters more than remaining target, system accepts only the remainder.

5. **Incomplete funding**
   - Contributions are pledge-based (no payment integration in v1).
   - If target is not reached, item remains partially funded.

6. **Item lifecycle**
   - Items with existing commitments are soft-archived, not hard-deleted.

7. **Realtime UX**
   - Reservation and contribution updates are pushed via WebSocket.
   - Client auto-refetches after realtime event to stay consistent.

8. **URL autofill**
   - Owner can paste product URL and auto-fetch title/image/price.
   - Manual editing remains available when metadata is partial.
