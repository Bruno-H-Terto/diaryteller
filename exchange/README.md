# Exchange service

Owns authorized context copies, uploads, recoverable results, deletion state and
the operational change feed for the Android client. The phone keeps the diary;
this service only stores what the user explicitly selected.

Configuration uses `EXCHANGE_*` environment variables. See `docs/android/` for
the contract and compose for the local stack.
