"""Local studio: a panel that shows and edits the running app and the stack.

Development tooling only. It is not a pod, it is not deployed and it must be
bound to loopback. It reads the app through the debug bridge (`adb forward`) and
the backend through the development database.
"""
