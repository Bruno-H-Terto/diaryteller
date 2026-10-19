// One restricted account per log writer; documents never contain diary content.
const logs = db.getSiblingDB("diary_logs");
for (const name of ["identity_logs", "conversation_logs", "speech_logs", "memory_logs", "notifications_logs"]) {
  logs.createUser({ user: name, pwd: name, roles: [{ role: "readWrite", db: "diary_logs" }] });
}
