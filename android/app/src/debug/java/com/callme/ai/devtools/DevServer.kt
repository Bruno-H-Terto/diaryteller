package com.callme.ai.devtools

import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.OutputStream
import java.net.InetAddress
import java.net.ServerSocket
import java.net.Socket
import kotlin.concurrent.thread

/**
 * Minimal loopback HTTP server for the studio panel.
 *
 * It runs on its own thread, answers one request per connection and never
 * touches the main thread, so the app keeps rendering while the panel inspects
 * it. Only the routes in [DevRoutes] exist.
 */
class DevServer(private val request: DevRequest) {

    private var socket: ServerSocket? = null

    fun start() {
        val server = ServerSocket(DevTools.PORT, BACKLOG, InetAddress.getByName("127.0.0.1"))
        socket = server
        thread(isDaemon = true, name = "dev-bridge") {
            while (!server.isClosed) {
                runCatching { handle(server.accept()) }
            }
        }
    }

    private fun handle(client: Socket) {
        client.use { connection ->
            val reader = BufferedReader(InputStreamReader(connection.getInputStream(), Charsets.UTF_8))
            val start = reader.readLine() ?: return
            val parts = start.split(' ')
            if (parts.size < 2) return
            val headers = mutableMapOf<String, String>()
            while (true) {
                val line = reader.readLine() ?: break
                if (line.isEmpty()) break
                val separator = line.indexOf(':')
                if (separator > 0) {
                    headers[line.take(separator).lowercase()] = line.substring(separator + 1).trim()
                }
            }
            val length = headers["content-length"]?.toIntOrNull() ?: 0
            val body = if (length > 0) CharArray(length).let { buffer ->
                var read = 0
                while (read < length) {
                    val count = reader.read(buffer, read, length - read)
                    if (count < 0) break
                    read += count
                }
                String(buffer, 0, read)
            } else {
                ""
            }
            val response = runCatching { request.answer(parts[0], parts[1], body) }
                .getOrElse { error ->
                    DevResponse(500, """{"error":${quote(error.message ?: "bridge failure")}}""")
                }
            write(connection.getOutputStream(), response)
        }
    }

    private fun write(out: OutputStream, response: DevResponse) {
        val bytes = response.body.toByteArray(Charsets.UTF_8)
        val head = buildString {
            append("HTTP/1.1 ${response.status} ${reason(response.status)}\r\n")
            append("Content-Type: application/json; charset=utf-8\r\n")
            append("Content-Length: ${bytes.size}\r\n")
            append("Access-Control-Allow-Origin: *\r\n")
            append("Access-Control-Allow-Headers: content-type\r\n")
            append("Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n")
            append("Connection: close\r\n\r\n")
        }
        out.write(head.toByteArray(Charsets.UTF_8))
        out.write(bytes)
        out.flush()
    }

    private fun reason(status: Int): String = when (status) {
        200 -> "OK"
        400 -> "Bad Request"
        404 -> "Not Found"
        else -> "Error"
    }

    private companion object {
        const val BACKLOG = 8
    }
}

/** One HTTP answer with a JSON body. */
class DevResponse(val status: Int, val body: String)

/** JSON string escaping, kept local so the bridge has no serialization model. */
fun quote(value: String): String = buildString {
    append('"')
    value.forEach { char ->
        when {
            char == '"' -> append("\\\"")
            char == '\\' -> append("\\\\")
            char == '\n' -> append("\\n")
            char == '\r' -> append("\\r")
            char == '\t' -> append("\\t")
            char < ' ' -> append("\\u%04x".format(char.code))
            else -> append(char)
        }
    }
    append('"')
}
