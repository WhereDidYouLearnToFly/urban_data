"""Live agent (Step 6) -- a SINGLE opencode session handling every incident,
one request at a time, but still routing each reply back to its own
incident's chat block in the Agents panel. Chosen over the earlier
one-opencode-session-per-incident design after that model was isolated as
the cause of a recurring segfault: even throttled, it still ended up with N
concurrent sessions/connections once a scenario ran long enough. A single
shared session means there is never more than one opencode/Ollama request
in flight, by construction -- not just rate-limited. Per-incident UI
routing still works because dispatch is strictly serial: whichever tag_id
is "in flight" is tracked and used to route that request's reply.

Trade-off: the model's own context is one shared conversation, not
per-incident isolated threads, so every message is prefixed with its
[tag_id] to keep incidents straight from the model's point of view.

MainWindow feeds create_incident() from agent_trigger group PDUs and
send_message() from the chat pane opened in AgentsPanel; replies come back
via incident_reply(tag_id, text, is_decision) -- is_decision is True only
for the reply to a brand-new incident's initial briefing (its "decision"),
not for later operator follow-up chat, so the UI can style/react to it
differently (see AgentsPanel.append_message).
"""
import json
import os
import subprocess

from PyQt5.QtCore import QObject, QProcess, QUrl, QTimer, pyqtSignal
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PORT = 51763
_BASE_URL = f"http://127.0.0.1:{_PORT}"


class AgentManager(QObject):
    incident_reply = pyqtSignal(str, str, bool)  # tag_id, reply_text, is_decision
    incident_error = pyqtSignal(str, str)         # tag_id, error message

    def __init__(self, parent=None):
        super().__init__(parent)
        self._net = QNetworkAccessManager(self)
        self._live_replies: set = set()   # keeps in-flight QNetworkReply objects referenced
        self._ready = False
        self._session_id = None            # the one shared opencode session
        self._creating_session = False

        # Single work queue -- (tag_id, text). _busy gates dispatch so a new
        # item never starts until the previous request's reply has come
        # back: never more than one opencode/Ollama call in flight at once,
        # regardless of how many incidents are active. Serial dispatch is
        # also what makes per-incident reply routing safe with only one
        # underlying session.
        self._queue: list[tuple] = []
        self._busy = False
        self._dispatch_timer = QTimer(self)
        self._dispatch_timer.setInterval(300)
        self._dispatch_timer.timeout.connect(self._dispatch_next)
        self._dispatch_timer.start()

        # A prior run that crashed/was killed ungracefully (this subsystem
        # has segfaulted before) can leave its own "opencode serve" child
        # orphaned and still holding _PORT. If that happens, THIS attempt to
        # start a fresh one on the same port silently fails to bind, but the
        # readiness poll below still succeeds -- against the stale orphan,
        # which has none of the current opencode.json/SKILL.md config, and
        # everything then fails with opaque 500s. Clear the port first so a
        # fresh process always wins.
        subprocess.run(
            ["pkill", "-f", f"opencode serve --port {_PORT}"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )

        self._process = QProcess(self)
        # explicit working directory, not inherited cwd -- opencode's config
        # discovery (which picks up the project-level opencode.json
        # registering mcp_server/incident_actions.py) depends on it, and
        # this app has been launched from both the project root and ui/
        # depending on how the user invoked it.
        self._process.setWorkingDirectory(_ROOT)
        self._process.start("opencode", ["serve", "--port", str(_PORT), "--hostname", "127.0.0.1"])

        self._ready_poll = QTimer(self)
        self._ready_poll.timeout.connect(self._check_ready)
        self._ready_poll.start(500)

    def shutdown(self):
        self._ready_poll.stop()
        self._dispatch_timer.stop()
        if self._process.state() != QProcess.NotRunning:
            self._process.terminate()
            self._process.waitForFinished(2000)

    # ── public API ──────────────────────────────────────────────────────────

    def create_incident(self, tag_id: str, summary: str, main_event: str):
        # No "start your reply with [tag_id]" instruction here -- the UI
        # (AgentsPanel.append_message) already prepends the tag on every
        # displayed message regardless of what the model writes. Asking the
        # model to also self-prefix produced a doubled "[tag] [tag] ..." any
        # time it actually complied.
        briefing = (
            f"New incident [{tag_id}]. Summary: {summary}\nConfirmed main event: {main_event}\n\n"
            f"Decide what this situation calls for and act on it now using your tools, "
            f"then report back per the format in your instructions."
        )
        self._queue.append((tag_id, briefing, True))

    def send_message(self, tag_id: str, text: str):
        self._queue.append((tag_id, f"[{tag_id}] {text}", False))

    # ── internal ────────────────────────────────────────────────────────────

    def _dispatch_next(self):
        if self._busy or not self._ready or not self._queue:
            return
        if self._session_id is None:
            self._create_session()
            return

        tag_id, text, is_decision = self._queue.pop(0)
        self._busy = True
        # "agent" selects the scoped incident-response persona defined in
        # opencode.json (own prompt from SKILL.md, no built-in coding
        # tools) -- letting the default "build" agent handle this instead
        # produced generic "I'm a coding assistant" refusals, since a bare
        # "system" field on a message only layers onto that agent's own
        # baked-in identity rather than replacing it.
        payload = {"parts": [{"type": "text", "text": text}], "agent": "incident-response"}
        reply = self._post(f"/session/{self._session_id}/message", json.dumps(payload).encode())
        self._live_replies.add(reply)
        reply.finished.connect(lambda: self._on_message_reply(reply, tag_id, is_decision))

    def _create_session(self):
        if self._creating_session:
            return
        self._creating_session = True
        body = json.dumps({"title": "Urban Data Incidents"}).encode()
        reply = self._post("/session", body)
        self._live_replies.add(reply)
        reply.finished.connect(lambda: self._on_session_created(reply))

    def _on_session_created(self, reply):
        self._creating_session = False
        self._live_replies.discard(reply)
        if reply.error() != reply.NoError:
            reply.deleteLater()
            return  # next dispatch tick will retry
        data = json.loads(bytes(reply.readAll()))
        self._session_id = data["id"]
        reply.deleteLater()

    def _check_ready(self):
        reply = self._net.get(QNetworkRequest(QUrl(f"{_BASE_URL}/session")))
        self._live_replies.add(reply)

        def on_done():
            if reply.error() == reply.NoError:
                self._ready = True
                self._ready_poll.stop()
            self._live_replies.discard(reply)
            reply.deleteLater()

        reply.finished.connect(on_done)

    def _post(self, path: str, body: bytes):
        request = QNetworkRequest(QUrl(f"{_BASE_URL}{path}"))
        request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
        return self._net.post(request, body)

    def _on_message_reply(self, reply, tag_id, is_decision):
        self._busy = False
        self._live_replies.discard(reply)
        if reply.error() != reply.NoError:
            self.incident_error.emit(tag_id, f"Agent request failed: {reply.errorString()}")
            reply.deleteLater()
            return
        data = json.loads(bytes(reply.readAll()))
        reply.deleteLater()
        text = "\n".join(
            part["text"] for part in data.get("parts", []) if part.get("type") == "text"
        ).strip()
        self.incident_reply.emit(tag_id, text or "(no reply)", is_decision)
