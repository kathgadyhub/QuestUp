import os
import re
import json
import time
import random
import string
import logging

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    session,
    flash
)

from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY


# ==========================================
# FLASK APP
# ==========================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "development-only-change-this-secret-key"
)

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = (
    os.environ.get("RENDER") is not None
)

logging.basicConfig(level=logging.INFO)


# ==========================================
# SUPABASE CONNECTION
# ==========================================

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# ==========================================
# SHARED HTML PIECES (all pages below are
# built into app.py, no extra template files)
# ==========================================

BASE_CSS = r'''
*{box-sizing:border-box}
body{margin:0;font-family:Arial,Helvetica,sans-serif;background:#f4f3ff;color:#1e1b3a}
.nav{background:linear-gradient(90deg,#5b3fd6,#3b82f6);padding:16px 28px;display:flex;justify-content:space-between;align-items:center}
.nav .brand{color:#fff;font-size:22px;font-weight:bold;text-decoration:none}
.nav a.link{color:#fff;text-decoration:none;margin-left:18px;font-weight:bold;font-size:14px}
.wrap{max-width:900px;margin:24px auto;padding:0 16px}
.card{background:#fff;border-radius:18px;padding:22px;margin:14px 0;box-shadow:0 2px 12px rgba(0,0,0,.07)}
.card h2,.card h3{margin-top:0}
.meta{color:#666;font-size:14px}
.center{text-align:center}
.btn{border:0;border-radius:12px;padding:12px 20px;cursor:pointer;background:#6d28d9;color:#fff;font-size:16px;font-weight:bold;text-decoration:none;display:inline-block}
.btn:disabled{opacity:.5;cursor:not-allowed}
.btn.red{background:#fee2e2;color:#b91c1c}
.btn.small{padding:8px 14px;font-size:14px;border-radius:10px}
.bigcode{font-size:64px;letter-spacing:10px;font-weight:bold;color:#6d28d9}
.chips{display:flex;flex-wrap:wrap;gap:10px;justify-content:center}
.chip{background:#ede9fe;border-radius:999px;padding:8px 14px;font-weight:bold}
.opts{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:14px 0}
.opt{border:0;border-radius:14px;padding:22px 12px;font-size:18px;font-weight:bold;color:#fff;text-align:center;cursor:pointer}
.opt:disabled{opacity:.5;cursor:not-allowed}
.o0{background:#e11d48}.o1{background:#2563eb}.o2{background:#d97706}.o3{background:#16a34a}
.timer{font-size:32px;font-weight:bold;color:#6d28d9}
.bar{height:10px;background:#e5e7eb;border-radius:99px;overflow:hidden;margin:8px 0 14px}
.bar>div{height:100%;background:#6d28d9;width:100%}
.row{display:flex;justify-content:space-between;align-items:center;padding:10px 14px;border-radius:12px;background:#f5f3ff;margin:6px 0}
.good{color:#16a34a}.bad{color:#dc2626}
input[type=text]{width:100%;padding:14px;border:2px solid #ddd6fe;border-radius:12px;font-size:18px;margin:8px 0}
.animals{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin:10px 0}
.animal{font-size:30px;background:#f5f3ff;border:3px solid transparent;border-radius:14px;padding:6px 10px;cursor:pointer}
.animal.sel{border-color:#6d28d9;background:#ede9fe}
.err{color:#b91c1c;font-weight:bold;min-height:22px}
@media(max-width:520px){.opts{grid-template-columns:1fr}.bigcode{font-size:44px}}
'''

NAV_HOST = r'''
<div class="nav"><a class="brand" href="/dashboard">QuizUp</a>
<div><a class="link" href="/dashboard">Dashboard</a><a class="link" href="/my-quizzes">My Quizzes</a><a class="link" href="/logout">Logout</a></div></div>
'''

NAV_PLAYER = r'''
<div class="nav"><a class="brand" href="/">QuizUp</a>
<div><a class="link" href="/join-game">Join Game</a></div></div>
'''


# ------------------------------------------
# MY QUIZZES PAGE
# ------------------------------------------

MY_QUIZZES_HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>QuizUp - My Quizzes</title>
<style>/*BASE_CSS*/
.card h3{margin:0 0 4px}
.qs{display:none;margin-top:12px;padding-left:18px}
.qs li{margin:8px 0}
.top{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px}
</style>
</head>
<body>
/*NAV*/
<div class="wrap">
  <div class="top">
    <h1>My Quizzes</h1>
    <a class="btn" href="/create-quiz">+ Create Quiz</a>
  </div>
  <div id="list">Loading...</div>
</div>

<script>
const list = document.getElementById("list");

function esc(s) {
  const d = document.createElement("div");
  d.textContent = s ?? "";
  return d.innerHTML;
}

async function loadQuizzes() {
  try {
    const res = await fetch("/api/my-quizzes");
    const data = await res.json();

    if (!res.ok) {
      list.textContent = data.error || "Something went wrong.";
      return;
    }

    if (!data.quizzes.length) {
      list.innerHTML = "<p>You have no quizzes yet. <a href='/create-quiz'>Create one</a>!</p>";
      return;
    }

    list.innerHTML = data.quizzes.map(q => `
      <div class="card">
        <h3>${esc(q.title)}</h3>
        <div class="meta">${esc(q.game_mode)} • ${(q.questions || []).length} question(s)</div>
        <div style="margin-top:8px">Game Code: <b style="color:#6d28d9;letter-spacing:3px;font-size:20px">${esc(q.join_code || "")}</b></div>
        <div style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap">
          <button class="btn small" onclick="hostGame('${q.id}')" ${(q.questions || []).length ? "" : "disabled"}>▶ Host Game</button>
          <button class="btn small" onclick="toggleQs('${q.id}')">View Questions</button>
          <button class="btn small red" onclick="deleteQuiz('${q.id}')">Delete</button>
        </div>
        <ol class="qs" id="qs-${q.id}">
          ${(q.questions || []).map(x => `
            <li>${esc(x.question)}<br>
                <span class="meta">Answer: ${esc(x.correct_answer)}</span></li>
          `).join("")}
        </ol>
      </div>
    `).join("");
  } catch (e) {
    list.textContent = "Could not load quizzes.";
  }
}

function toggleQs(id) {
  const el = document.getElementById("qs-" + id);
  el.style.display = el.style.display === "block" ? "none" : "block";
}

async function hostGame(id) {
  const res = await fetch("/api/host-game/" + id, { method: "POST" });
  const data = await res.json();
  if (res.ok) location.href = "/host/" + data.code;
  else alert(data.error || "Could not start the game.");
}

async function deleteQuiz(id) {
  if (!confirm("Delete this quiz and all its questions?")) return;
  const res = await fetch("/api/quizzes/" + id, { method: "DELETE" });
  if (res.ok) loadQuizzes();
  else alert("Could not delete the quiz.");
}

loadQuizzes();
</script>
</body>
</html>
'''

# ------------------------------------------
# HOST PAGE (lobby, questions, leaderboard)
# ------------------------------------------

HOST_HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>QuizUp - Host Game</title>
<style>/*BASE_CSS*/</style>
</head>
<body>
/*NAV*/
<div class="wrap" id="app">Loading...</div>

<script>
const code = location.pathname.split("/").pop();
let state = null, lastSync = 0, lastSig = "", polledAtZero = false;

function esc(s) {
  const d = document.createElement("div");
  d.textContent = s ?? "";
  return d.innerHTML;
}

function medal(i) { return i === 0 ? "🥇" : i === 1 ? "🥈" : i === 2 ? "🥉" : (i + 1) + "."; }

function teamBoard(teams) {
  if (!teams || !teams.length) return "";
  return "<h3>Team Standings</h3>" + teams.map((t, i) =>
    `<div class="row"><span>${medal(i)} ${t.emoji} <b>${esc(t.name)}</b> <span class="meta">(${t.count} player${t.count === 1 ? "" : "s"})</span></span><b>${t.score}</b></div>`
  ).join("");
}

function board(players, limit) {
  return players.slice(0, limit).map((p, i) =>
    `<div class="row"><span>${medal(i)} ${esc(p.animal)} ${esc(p.name)}${p.team_label ? ' <span class="meta">' + esc(p.team_label) + "</span>" : ""}</span><b>${p.score}</b></div>`
  ).join("");
}

async function poll() {
  try {
    const res = await fetch("/api/host/" + code + "/state");
    const data = await res.json();
    if (!res.ok) {
      document.getElementById("app").innerHTML = '<div class="card">' + esc(data.error || "Error") + '</div>';
      return;
    }
    state = data;
    lastSync = performance.now();
    render();
  } catch (e) {}
}

function render() {
  const s = state;
  const sig = [s.status, s.current_index, s.time_up, s.player_count, s.answered_count].join("|");
  if (sig !== lastSig) {
    lastSig = sig;
    polledAtZero = false;
    draw(s);
  }
}

function draw(s) {
  const app = document.getElementById("app");

  if (s.status === "lobby") {
    app.innerHTML = `
      <div class="card center">
        <div class="meta">${esc(s.title)}</div>
        <p>Join at <b>${esc(location.origin)}/join-game</b> using the game code</p>
        <div class="bigcode">${esc(s.code)}</div>
        <p><b>${s.player_count}</b> player(s) joined</p>
        <div class="chips">${s.players.map(p => `<span class="chip">${esc(p.animal)} ${esc(p.name)}${p.team_label ? " • " + esc(p.team_label) : ""}</span>`).join("")}</div>
        <p><button class="btn" ${s.player_count ? "" : "disabled"} onclick="act('start')">▶ Start Game</button></p>
      </div>`;
    return;
  }

  if (s.status === "active" && s.question) {
    const q = s.question;
    const last = s.current_index >= s.total - 1;
    let opts = "";
    if (q.options.length) {
      opts = '<div class="opts">' + q.options.map((o, i) => {
        const right = s.time_up && s.correct_answer && o.trim().toLowerCase() === s.correct_answer.trim().toLowerCase();
        const dim = s.time_up && !right ? "opacity:.35;" : "";
        return `<div class="opt o${i}" style="${dim}cursor:default">${right ? "✔ " : ""}${esc(o)}</div>`;
      }).join("") + "</div>";
    }
    const scrambled = q.scrambled ? `<div class="bigcode" style="font-size:42px">${esc(q.scrambled)}</div>` : "";
    const reveal = s.time_up && !q.options.length
      ? `<p class="center"><b>Correct answer:</b> <span class="good">${esc(s.correct_answer)}</span></p>` : "";
    const lb = s.time_up ? teamBoard(s.teams) + `<h3>Leaderboard</h3>${board(s.players, 5)}` : "";

    app.innerHTML = `
      <div class="card">
        <div class="row"><b>Question ${s.current_index + 1} / ${s.total}</b><span class="timer" id="timer"></span></div>
        <div class="bar"><div id="barfill"></div></div>
        <h2>${esc(q.text)}</h2>
        ${scrambled}
        ${opts}
        ${reveal}
        <p class="center meta">${s.answered_count} / ${s.player_count} answered</p>
        ${lb}
        <p class="center"><button class="btn" onclick="act('next')">${last ? "🏁 Finish Game" : (s.time_up ? "Next Question ▶" : "Skip ⏭")}</button></p>
      </div>`;
    tick();
    return;
  }

  if (s.status === "finished") {
    app.innerHTML = `
      <div class="card">
        <h2 class="center">🏁 Final Leaderboard</h2>
        ${teamBoard(s.teams)}
        <h3>Players</h3>
        ${board(s.players, 50) || "<p class='center'>No players.</p>"}
        <p class="center"><a class="btn" href="/leaderboard?code=${esc(s.code)}">🏆 Full Leaderboard</a> <a class="btn" href="/my-quizzes">Back to My Quizzes</a></p>
      </div>`;
  }
}

function tick() {
  const s = state;
  if (!s || s.status !== "active" || !s.question) return;
  const t = document.getElementById("timer");
  const bar = document.getElementById("barfill");
  if (!t || !bar) return;

  const remaining = s.question.remaining - (performance.now() - lastSync) / 1000;
  if (s.time_up) {
    t.textContent = "Time's up!";
    bar.style.width = "0%";
    return;
  }
  t.textContent = Math.max(0, Math.ceil(remaining)) + "s";
  bar.style.width = Math.max(0, remaining / s.question.timer * 100) + "%";
  if (remaining <= 0 && !polledAtZero) { polledAtZero = true; poll(); }
}

async function act(what) {
  await fetch("/api/host/" + code + "/" + what, { method: "POST" });
  poll();
}

setInterval(poll, 2000);
setInterval(tick, 250);
poll();
</script>
</body>
</html>
'''

# ------------------------------------------
# JOIN GAME PAGE
# ------------------------------------------

JOIN_HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>QuizUp - Join Game</title>
<style>/*BASE_CSS*/</style>
</head>
<body>
/*NAV*/
<div class="wrap" style="max-width:520px">
  <div class="card center">
    <h2>🎮 Join Game</h2>
    <input type="text" id="code" placeholder="Game code" maxlength="6" inputmode="numeric">
    <input type="text" id="name" placeholder="Your name" maxlength="20">
    <p class="meta">Choose your animal</p>
    <div class="animals" id="animals"></div>
    <div id="teamBox" style="display:none">
      <p class="meta">Choose your team</p>
      <div class="animals" id="teams"></div>
    </div>
    <div class="err" id="err"></div>
    <button class="btn" id="go" onclick="join()">Join</button>
  </div>
</div>

<script>
const ANIMALS = ["🦁","🐼","🐯","🐵","🐸","🐧","🦊","🐨","🐰","🐶","🐱","🦄"];
let animal = ANIMALS[0];

const box = document.getElementById("animals");
box.innerHTML = ANIMALS.map(a => `<span class="animal ${a === animal ? "sel" : ""}" data-a="${a}">${a}</span>`).join("");
box.addEventListener("click", e => {
  const a = e.target.dataset.a;
  if (!a) return;
  animal = a;
  [...box.children].forEach(c => c.classList.toggle("sel", c.dataset.a === a));
});

const params = new URLSearchParams(location.search);
if (params.get("code")) document.getElementById("code").value = params.get("code");

let team = "";
const TEAM_LIST = [["red", "🔴 Red"], ["blue", "🔵 Blue"], ["green", "🟢 Green"], ["yellow", "🟡 Yellow"]];
const teamsBox = document.getElementById("teams");
teamsBox.innerHTML = TEAM_LIST.map(t =>
  `<span class="animal" style="font-size:18px;font-weight:bold" data-t="${t[0]}">${t[1]}</span>`).join("");
teamsBox.addEventListener("click", e => {
  const t = e.target.dataset.t;
  if (!t) return;
  team = t;
  [...teamsBox.children].forEach(c => c.classList.toggle("sel", c.dataset.t === t));
});

async function checkMode() {
  const c = document.getElementById("code").value.trim();
  const box = document.getElementById("teamBox");
  if (c.length !== 6) { box.style.display = "none"; return; }
  try {
    const r = await fetch("/api/game-info?code=" + encodeURIComponent(c));
    const d = await r.json();
    box.style.display = d.found && d.mode === "team" ? "block" : "none";
  } catch (e) {}
}
document.getElementById("code").addEventListener("input", checkMode);
checkMode();

async function join() {
  const err = document.getElementById("err");
  err.textContent = "";
  const btn = document.getElementById("go");
  btn.disabled = true;
  try {
    const res = await fetch("/api/join", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        code: document.getElementById("code").value,
        name: document.getElementById("name").value,
        animal: animal,
        team: team
      })
    });
    const data = await res.json();
    if (res.ok) { location.href = "/play"; return; }
    err.textContent = data.error || "Could not join.";
  } catch (e) {
    err.textContent = "Could not join. Try again.";
  }
  btn.disabled = false;
}
</script>
</body>
</html>
'''

# ------------------------------------------
# PLAY PAGE (player screen)
# ------------------------------------------

PLAY_HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>QuizUp - Play</title>
<style>/*BASE_CSS*/</style>
</head>
<body>
/*NAV*/
<div class="wrap" style="max-width:700px" id="app">Loading...</div>

<script>
let state = null, lastSync = 0, lastSig = "", polledAtZero = false, submitting = false;

function esc(s) {
  const d = document.createElement("div");
  d.textContent = s ?? "";
  return d.innerHTML;
}

function medal(i) { return i === 0 ? "🥇" : i === 1 ? "🥈" : i === 2 ? "🥉" : (i + 1) + "."; }

function teamBoard(teams) {
  if (!teams || !teams.length) return "";
  return "<h3>Team Standings</h3>" + teams.map((t, i) =>
    `<div class="row"><span>${medal(i)} ${t.emoji} <b>${esc(t.name)}</b> <span class="meta">(${t.count} player${t.count === 1 ? "" : "s"})</span></span><b>${t.score}</b></div>`
  ).join("");
}

function board(players, limit) {
  return players.slice(0, limit).map((p, i) =>
    `<div class="row"><span>${medal(i)} ${esc(p.animal)} ${esc(p.name)}${p.team_label ? ' <span class="meta">' + esc(p.team_label) + "</span>" : ""}</span><b>${p.score}</b></div>`
  ).join("");
}

async function poll() {
  try {
    const res = await fetch("/api/play/state");
    if (res.status === 401 || res.status === 404) { location.href = "/join-game"; return; }
    state = await res.json();
    lastSync = performance.now();
    render();
  } catch (e) {}
}

function render() {
  const s = state, me = s.me || {};
  const locked = s.my_answer && s.my_answer.locked ? 1 : 0;
  const sig = [s.status, s.current_index, s.time_up, locked, me.score, me.rank, s.status === "lobby" ? s.player_count : ""].join("|");
  if (sig !== lastSig) {
    lastSig = sig;
    polledAtZero = false;
    draw(s, me);
  }
}

function header(me) {
  return `<div class="row"><span>${esc(me.animal)} <b>${esc(me.name)}</b>${me.team_label ? " • " + esc(me.team_label) : ""}</span><span><b>${me.score}</b> pts • #${me.rank}</span></div>`;
}

function draw(s, me) {
  const app = document.getElementById("app");

  if (s.status === "lobby") {
    app.innerHTML = header(me) + `
      <div class="card center">
        <h2>You're in! 🎉</h2>
        <p>Waiting for the host to start the game...</p>
        <p class="meta">${s.player_count} player(s) in the lobby</p>
      </div>`;
    return;
  }

  if (s.status === "active" && s.question) {
    const q = s.question;

    if (!s.time_up && s.my_answer && s.my_answer.locked) {
      app.innerHTML = header(me) + `
        <div class="card center">
          <div class="timer" id="timer"></div>
          <div class="bar"><div id="barfill"></div></div>
          <h2>Answer locked in ✅</h2>
          <p>Waiting for the others...</p>
        </div>`;
      tick();
      return;
    }

    if (!s.time_up) {
      let input = "";
      if (q.options.length) {
        input = '<div class="opts">' + q.options.map((o, i) =>
          `<button class="opt o${i}" onclick="submitAnswer(${i})">${esc(o)}</button>`).join("") + "</div>";
      } else {
        const scr = q.scrambled ? `<div class="bigcode" style="font-size:40px">${esc(q.scrambled)}</div>` : "";
        input = scr + `<input type="text" id="ans" placeholder="Type your answer" autocomplete="off">
          <button class="btn" onclick="submitText()">Submit</button>`;
      }
      app.innerHTML = header(me) + `
        <div class="card">
          <div class="row"><b>Question ${s.current_index + 1} / ${s.total}</b><span class="timer" id="timer"></span></div>
          <div class="bar"><div id="barfill"></div></div>
          <h2>${esc(q.text)}</h2>
          ${input}
        </div>`;
      const box = document.getElementById("ans");
      if (box) box.addEventListener("keydown", e => { if (e.key === "Enter") submitText(); });
      tick();
      return;
    }

    const a = s.my_answer;
    const verdict = a ? (a.correct ? '<span class="good">✅ Correct!</span>' : '<span class="bad">❌ Wrong</span>') : "⏰ No answer";
    app.innerHTML = header(me) + `
      <div class="card center">
        <h2>${verdict}</h2>
        <p>${a ? "+" + a.points + " points" : "+0 points"}</p>
        <p><b>Correct answer:</b> ${esc(s.correct_answer)}</p>
        <p class="meta">Waiting for the host to continue...</p>
      </div>`;
    return;
  }

  if (s.status === "finished") {
    app.innerHTML = header(me) + `
      <div class="card">
        <h2 class="center">🏁 Game Over</h2>
        <p class="center">You placed <b>#${me.rank}</b> with <b>${me.score}</b> points.</p>
        ${teamBoard(s.teams)}
        ${board(s.players, 5)}
        <p class="center"><a class="btn" href="/leaderboard?code=${esc(s.code)}">🏆 Full Leaderboard</a> <a class="btn" href="/join-game">Join another game</a></p>
      </div>`;
  }
}

function tick() {
  const s = state;
  if (!s || s.status !== "active" || !s.question || s.time_up) return;
  const t = document.getElementById("timer");
  const bar = document.getElementById("barfill");
  if (!t || !bar) return;
  const remaining = s.question.remaining - (performance.now() - lastSync) / 1000;
  t.textContent = Math.max(0, Math.ceil(remaining)) + "s";
  bar.style.width = Math.max(0, remaining / s.question.timer * 100) + "%";
  if (remaining <= 0 && !polledAtZero) { polledAtZero = true; poll(); }
}

async function sendAnswer(text) {
  if (submitting) return;
  submitting = true;
  try {
    const res = await fetch("/api/play/answer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ answer: text })
    });
    if (!res.ok && res.status !== 409) {
      const data = await res.json();
      alert(data.error || "Could not send your answer.");
    }
  } catch (e) {}
  submitting = false;
  poll();
}

function submitAnswer(i) { sendAnswer(state.question.options[i]); }

function submitText() {
  const v = (document.getElementById("ans").value || "").trim();
  if (v) sendAnswer(v);
}

setInterval(poll, 2000);
setInterval(tick, 250);
poll();
</script>
</body>
</html>
'''


LEADERBOARD_HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>QuizUp - Leaderboard</title>
<style>/*BASE_CSS*/
.podium{display:flex;gap:14px;justify-content:center;align-items:flex-end;margin:24px 0}
.pod{flex:1;max-width:240px;background:#fff;border-radius:20px;padding:18px 10px;text-align:center;box-shadow:0 4px 16px rgba(0,0,0,.08)}
.pod .av{font-size:54px}
.pod .nm{font-weight:bold;font-size:20px;word-break:break-word}
.pod .sc{font-size:34px;font-weight:bold;color:#6d28d9}
.p1{padding-top:40px;padding-bottom:40px;border:2px solid #c4b5fd}
.p3{padding-top:12px;padding-bottom:12px}
.rank{background:#ede9fe;border-radius:10px;padding:6px 12px;font-weight:bold;margin-right:12px}
</style>
</head>
<body>
/*NAV*/
<div class="wrap" id="app">Loading...</div>

<script>
const params = new URLSearchParams(location.search);
const code = params.get("code") || "";
const app = document.getElementById("app");

function esc(s) {
  const d = document.createElement("div");
  d.textContent = s ?? "";
  return d.innerHTML;
}

function pod(p, rank, cls) {
  if (!p) return "";
  const icon = rank === 1 ? "🏆" : rank === 2 ? "🥈" : "🥉";
  return `<div class="pod ${cls}">
    <div style="font-size:26px">${icon}</div>
    <div class="av">${esc(p.animal)}</div>
    <div class="nm">${esc(p.name)}</div>
    <div class="sc">${p.score}</div>
    ${rank === 1 ? '<div class="meta">WINNER</div>' : ""}
  </div>`;
}

function render(d) {
  const pl = d.players;
  const status = d.status === "finished" ? "Final results" : d.status === "active" ? "Game in progress" : "Waiting to start";

  if (!pl.length) {
    app.innerHTML = `<div class="card center"><h1>🏆 Leaderboard</h1><p class="meta">${esc(d.title)}</p><p>No players yet.</p></div>`;
    return;
  }

  const teamHtml = (d.teams && d.teams.length)
    ? '<div class="card"><h3>Team Standings</h3>' + d.teams.map((t, i) =>
        `<div class="row"><span>${i + 1}. ${t.emoji} <b>${esc(t.name)}</b> <span class="meta">(${t.count} player${t.count === 1 ? "" : "s"})</span></span><b style="color:#6d28d9">${t.score} pts</b></div>`
      ).join("") + "</div>"
    : "";

  app.innerHTML = `
    <div class="center">
      <h1 style="margin-bottom:4px">🏆 Leaderboard</h1>
      <div class="meta">${esc(d.title)} • Code ${esc(d.code)} • ${status}</div>
    </div>
    ${teamHtml}
    <div class="podium">${pod(pl[1], 2, "p2")}${pod(pl[0], 1, "p1")}${pod(pl[2], 3, "p3")}</div>
    ${pl.slice(3).map((p, i) => `
      <div class="row"><span><span class="rank">${i + 4}</span>${esc(p.animal)} <b>${esc(p.name)}</b></span><b style="color:#6d28d9">${p.score} pts</b></div>
    `).join("")}`;
}

async function load() {
  try {
    const res = await fetch("/api/leaderboard" + (code ? "?code=" + encodeURIComponent(code) : ""));
    const d = await res.json();
    if (!res.ok) {
      app.innerHTML = '<div class="card center">' + esc(d.error || "No leaderboard yet.") + "</div>";
      return;
    }
    render(d);
  } catch (e) {}
}

setInterval(load, 3000);
load();
</script>
</body>
</html>
'''


def build_page(html, nav):
    return html.replace("/*BASE_CSS*/", BASE_CSS).replace("/*NAV*/", nav)


MY_QUIZZES_PAGE = build_page(MY_QUIZZES_HTML, NAV_HOST)
HOST_PAGE = build_page(HOST_HTML, NAV_HOST)
JOIN_PAGE = build_page(JOIN_HTML, NAV_PLAYER)
PLAY_PAGE = build_page(PLAY_HTML, NAV_PLAYER)
LEADERBOARD_PAGE = build_page(LEADERBOARD_HTML, NAV_PLAYER)


# ==========================================
# GAME HELPERS
# ==========================================

QUESTION_CACHE = {}

TEAMS = {
    "red": {"name": "Red", "emoji": "🔴"},
    "blue": {"name": "Blue", "emoji": "🔵"},
    "green": {"name": "Green", "emoji": "🟢"},
    "yellow": {"name": "Yellow", "emoji": "🟡"}
}


def now_ms():
    return int(time.time() * 1000)


def parse_choices(value):
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except Exception:
            value = {}
    return value if isinstance(value, dict) else {}


def scramble_text(text, seed):
    rng = random.Random(seed)
    words = []

    for word in text.split(" "):
        letters = list(word)

        if len(set(letters)) > 1:
            original = letters[:]
            for _ in range(10):
                rng.shuffle(letters)
                if letters != original:
                    break

        words.append("".join(letters))

    return " ".join(words)


def normalize_question(row, index):
    choices = parse_choices(row.get("choices"))
    question_type = row.get("question_type") or ""

    try:
        timer = int(choices.get("timer", 30))
    except (ValueError, TypeError):
        timer = 30

    timer = max(5, min(timer, 300))

    options = []

    if question_type == "multiple_choice":
        options = [str(choices.get(key, "")) for key in "ABCD"]
    elif question_type == "true_false":
        options = ["True", "False"]

    correct = str(row.get("correct_answer", ""))

    scrambled = None
    if question_type == "jumbled":
        scrambled = scramble_text(correct, str(row.get("id", index)))

    return {
        "index": index,
        "text": str(row.get("question", "")),
        "type": question_type,
        "correct": correct,
        "options": options,
        "timer": timer,
        "scrambled": scrambled
    }


def load_questions(game):
    key = game["id"]

    if key in QUESTION_CACHE:
        return QUESTION_CACHE[key]

    try:
        rows = (
            supabase.table("questions")
            .select("*")
            .eq("quiz_id", game["quiz_id"])
            .order("created_at")
            .order("id")
            .execute()
            .data
        )
    except Exception:
        rows = (
            supabase.table("questions")
            .select("*")
            .eq("quiz_id", game["quiz_id"])
            .order("id")
            .execute()
            .data
        )

    questions = [
        normalize_question(row, index)
        for index, row in enumerate(rows or [])
    ]

    QUESTION_CACHE[key] = questions
    return questions


def get_game(code):
    code = str(code or "").strip()

    if not code:
        return None

    result = (
        supabase.table("games")
        .select("*")
        .eq("code", code)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    return result.data[0] if result.data else None


def get_game_by_id(game_id):

    if not game_id:
        return None

    result = (
        supabase.table("games")
        .select("*")
        .eq("id", game_id)
        .limit(1)
        .execute()
    )

    return result.data[0] if result.data else None


def join_code_taken(code):
    result = (
        supabase.table("quizzes")
        .select("id")
        .eq("join_code", code)
        .limit(1)
        .execute()
    )

    return bool(result.data)


def generate_join_code():
    for _ in range(30):
        candidate = "".join(random.choices(string.digits, k=6))

        if not join_code_taken(candidate):
            return candidate

    raise RuntimeError("Could not generate a unique game code.")


def get_pending_join_code():
    """The code shown on the Create Quiz page; it is given to the next saved quiz."""

    code = session.get("pending_join_code")

    if not code or join_code_taken(code):
        code = generate_join_code()
        session["pending_join_code"] = code

    return code


def host_game_or_error(code):
    if not session.get("user_id"):
        return None, (jsonify({"error": "Please log in first."}), 401)

    game = get_game(code)

    if not game or game["host_id"] != session["user_id"]:
        return None, (jsonify({"error": "Game not found."}), 404)

    return game, None


def compute_teams(game, players):
    """Adds team_label to each player and returns team totals (team mode only)."""

    for player in players:
        key = player.get("team")

        if key in TEAMS:
            player["team_label"] = (
                TEAMS[key]["emoji"] + " " + TEAMS[key]["name"]
            )
        else:
            player["team_label"] = ""

    if game.get("game_mode") != "team":
        return []

    totals = {}

    for player in players:
        key = player.get("team")

        if key not in TEAMS:
            continue

        team = totals.setdefault(key, {
            "key": key,
            "name": TEAMS[key]["name"],
            "emoji": TEAMS[key]["emoji"],
            "score": 0,
            "count": 0
        })

        team["score"] += player.get("score") or 0
        team["count"] += 1

    return sorted(totals.values(), key=lambda t: -t["score"])


def build_state(game, viewer_player_id=None):
    questions = load_questions(game)
    total = len(questions)

    players = (
        supabase.table("players")
        .select("id,name,animal,score,team")
        .eq("game_id", game["id"])
        .order("score", desc=True)
        .order("joined_at")
        .execute()
        .data
        or []
    )

    teams = compute_teams(game, players)

    state = {
        "code": game["code"],
        "title": game.get("quiz_title") or "Quiz",
        "status": game["status"],
        "game_mode": game.get("game_mode"),
        "teams": teams,
        "total": total,
        "current_index": game["current_index"],
        "players": players,
        "player_count": len(players),
        "question": None,
        "time_up": False,
        "answered_count": 0,
        "correct_answer": None,
        "my_answer": None
    }

    if viewer_player_id:
        for rank, player in enumerate(players, start=1):
            if str(player["id"]) == str(viewer_player_id):
                me = dict(player)
                me["rank"] = rank
                state["me"] = me
                break

    index = game["current_index"]

    if game["status"] == "active" and 0 <= index < total:
        q = questions[index]

        started = int(game.get("question_started_ms") or now_ms())
        elapsed = (now_ms() - started) / 1000
        remaining = max(0.0, q["timer"] - elapsed)

        answers = (
            supabase.table("answers")
            .select("player_id,is_correct,points")
            .eq("game_id", game["id"])
            .eq("question_index", index)
            .execute()
            .data
            or []
        )

        answered = len(answers)

        time_up = remaining <= 0 or (
            len(players) > 0 and answered >= len(players)
        )

        state["question"] = {
            "index": index,
            "text": q["text"],
            "type": q["type"],
            "options": q["options"],
            "scrambled": q["scrambled"],
            "timer": q["timer"],
            "remaining": remaining
        }

        state["time_up"] = time_up
        state["answered_count"] = answered

        if time_up:
            state["correct_answer"] = q["correct"]

        if viewer_player_id:
            mine = next(
                (
                    a for a in answers
                    if str(a["player_id"]) == str(viewer_player_id)
                ),
                None
            )

            if mine:
                if time_up:
                    state["my_answer"] = {
                        "locked": True,
                        "correct": bool(mine["is_correct"]),
                        "points": mine["points"]
                    }
                else:
                    state["my_answer"] = {"locked": True}

    return state


def add_my_quizzes_link(html):
    """Adds a My Quizzes link to the dashboard without editing dashboard.html."""

    if "/my-quizzes" in html:
        return html

    try:
        match = re.search(
            r"<a\b[^>]*>\s*Dashboard\s*</a>",
            html,
            re.IGNORECASE
        )

        if match:
            anchor = match.group(0)
            new_anchor = re.sub(
                r"""href=["'][^"']*["']""",
                'href="/my-quizzes"',
                anchor,
                count=1
            )
            new_anchor = re.sub(
                r"Dashboard", "My Quizzes", new_anchor, count=1
            )
            new_anchor = re.sub(r"\bactive\b", "", new_anchor)
            return html.replace(anchor, anchor + new_anchor, 1)
    except Exception:
        app.logger.exception("Could not add My Quizzes link")

    floating = (
        '<a href="/my-quizzes" style="position:fixed;right:20px;'
        "bottom:20px;background:#6d28d9;color:#fff;padding:12px 18px;"
        "border-radius:12px;text-decoration:none;font-weight:bold;"
        'z-index:9999">📚 My Quizzes</a>'
    )

    if "</body>" in html:
        return html.replace("</body>", floating + "</body>", 1)

    return html + floating


JOIN_CODE_BANNER = r'''
<div id="join-code-banner" style="background:#ede9fe;border:2px dashed #6d28d9;border-radius:16px;padding:14px 18px;margin:16px 0;">
  <div id="jc-label" style="font-size:13px;color:#4c1d95;font-weight:bold;letter-spacing:1px">YOUR GAME CODE</div>
  <div id="jc-code" style="font-size:40px;letter-spacing:8px;font-weight:bold;color:#6d28d9">__CODE__</div>
  <div id="jc-note" style="font-size:14px;color:#555">Players type this code in Join Game to play this quiz. Save the quiz, then press Host Game in My Quizzes to open the game.</div>
</div>
<script>
(function () {
  var label = document.getElementById("jc-label");
  var codeEl = document.getElementById("jc-code");
  var note = document.getElementById("jc-note");
  var orig = window.fetch.bind(window);

  window.fetch = async function (input, init) {
    var res = await orig(input, init);
    try {
      var url = typeof input === "string" ? input : ((input && input.url) || "");
      if (url.indexOf("/api/create-quiz") !== -1 && res.ok) {
        var data = await res.clone().json();
        if (data.join_code) {
          label.textContent = "QUIZ SAVED - GAME CODE";
          codeEl.textContent = data.join_code;
          note.textContent = "Open My Quizzes and press Host Game. Players join with this code.";
          setTimeout(async function () {
            try {
              var r = await orig("/api/new-join-code");
              var d = await r.json();
              if (d.code) {
                label.textContent = "GAME CODE FOR YOUR NEXT QUIZ";
                codeEl.textContent = d.code;
                note.textContent = "Players type this code in Join Game to play the next quiz you save.";
              }
            } catch (e) {}
          }, 6000);
        }
      }
    } catch (e) {}
    return res;
  };
})();
</script>
'''


def add_join_code_banner(html, code):
    banner = JOIN_CODE_BANNER.replace("__CODE__", code)

    if re.search(r"</h1>", html, re.IGNORECASE):
        return re.sub(
            r"</h1>", lambda m: m.group(0) + banner, html,
            count=1, flags=re.IGNORECASE
        )

    if re.search(r"<body[^>]*>", html, re.IGNORECASE):
        return re.sub(
            r"<body[^>]*>", lambda m: m.group(0) + banner, html,
            count=1, flags=re.IGNORECASE
        )

    return banner + html


# ==========================================
# HOME
# ==========================================

@app.route("/")
def home():
    return render_template("index.html")


# ==========================================
# LOGIN
# ==========================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not email or not password:
        flash("Please enter your email and password.", "error")
        return render_template("login.html"), 400

    try:
        result = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if not result.user:
            flash("Login failed. Please try again.", "error")
            return render_template("login.html"), 401

        # Create a new session after successful login.
        session.clear()
        session["user_id"] = str(result.user.id)
        session["user_email"] = result.user.email or email

        flash("Login successful!", "success")
        return redirect(url_for("dashboard"))

    except Exception:
        app.logger.exception("Login failed")

        flash(
            "Login failed. Check your email and password. "
            "If you registered recently, verify your email first.",
            "error"
        )

        return render_template("login.html"), 401


# ==========================================
# REGISTER
# ==========================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":
        return render_template("register.html")

    full_name = (
        request.form.get("full_name")
        or request.form.get("name")
        or ""
    ).strip()

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not full_name or not email or not password:
        flash("Please complete all required fields.", "error")
        return render_template("register.html"), 400

    if len(password) < 6:
        flash(
            "Password must be at least 6 characters long.",
            "error"
        )
        return render_template("register.html"), 400

    try:
        result = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "full_name": full_name
                }
            }
        })

        if not result.user:
            flash("Registration failed. Please try again.", "error")
            return render_template("register.html"), 400

        # Supabase may require email verification.
        if result.session:
            session.clear()
            session["user_id"] = str(result.user.id)
            session["user_email"] = result.user.email or email

            flash("Registration successful!", "success")
            return redirect(url_for("dashboard"))

        flash(
            "Registration successful! Check your email "
            "to verify your account before logging in.",
            "success"
        )
        return redirect(url_for("login"))

    except Exception:
        app.logger.exception("Registration failed")

        flash(
            "Registration failed. The email may already exist, "
            "or Supabase Auth may need checking.",
            "error"
        )

        return render_template("register.html"), 400


# ==========================================
# LOGOUT
# ==========================================

@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    return redirect(url_for("home"))


# ==========================================
# DASHBOARD
# ==========================================

@app.route("/dashboard")
def dashboard():

    if not session.get("user_id"):
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    html = render_template("dashboard.html")
    return add_my_quizzes_link(html)


# ==========================================
# CREATE QUIZ PAGE
# ==========================================

@app.route("/create-quiz")
def create_quiz():

    if not session.get("user_id"):
        return redirect(url_for("login"))

    html = render_template("create_quiz.html")

    try:
        html = add_join_code_banner(html, get_pending_join_code())
    except Exception:
        app.logger.exception(
            "Could not show the game code (is quizzes.join_code created?)"
        )

    return html


@app.route("/api/new-join-code")
def api_new_join_code():

    if not session.get("user_id"):
        return jsonify({"error": "Please log in first."}), 401

    try:
        return jsonify({"code": get_pending_join_code()}), 200
    except Exception:
        app.logger.exception("New join code failed")
        return jsonify({"error": "Could not get a code."}), 500


# ==========================================
# MY QUIZZES (PAGE + API)
# ==========================================

@app.route("/my-quizzes")
def my_quizzes():

    if not session.get("user_id"):
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    return MY_QUIZZES_PAGE


@app.route("/api/my-quizzes")
def api_my_quizzes():

    if not session.get("user_id"):
        return jsonify({"error": "Please log in first."}), 401

    try:
        result = (
            supabase.table("quizzes")
            .select("*, questions(*)")
            .eq("host_id", session["user_id"])
            .order("created_at", desc=True)
            .execute()
        )
        quizzes = result.data or []

        for quiz in quizzes:
            if not quiz.get("join_code"):
                code = generate_join_code()

                supabase.table("quizzes").update({
                    "join_code": code
                }).eq("id", quiz["id"]).execute()

                quiz["join_code"] = code

        return jsonify({"quizzes": quizzes}), 200

    except Exception:
        app.logger.exception("Load my quizzes failed")
        return jsonify({"error": "Could not load your quizzes."}), 500


@app.route("/api/quizzes/<quiz_id>", methods=["DELETE"])
def api_delete_quiz(quiz_id):

    if not session.get("user_id"):
        return jsonify({"error": "Please log in first."}), 401

    try:
        # Make sure the quiz belongs to the logged-in user.
        owned = (
            supabase.table("quizzes")
            .select("id")
            .eq("id", quiz_id)
            .eq("host_id", session["user_id"])
            .execute()
        )

        if not owned.data:
            return jsonify({"error": "Quiz not found."}), 404

        try:
            supabase.table("games").delete().eq(
                "quiz_id", str(quiz_id)
            ).execute()
        except Exception:
            app.logger.exception("Could not delete games of quiz")

        supabase.table("questions").delete().eq(
            "quiz_id", quiz_id
        ).execute()

        supabase.table("quizzes").delete().eq(
            "id", quiz_id
        ).execute()

        return jsonify({"success": True}), 200

    except Exception:
        app.logger.exception("Delete quiz failed")
        return jsonify({"error": "Could not delete the quiz."}), 500


# ==========================================
# HOST A GAME
# ==========================================

@app.route("/api/host-game/<quiz_id>", methods=["POST"])
def api_host_game(quiz_id):

    if not session.get("user_id"):
        return jsonify({"error": "Please log in first."}), 401

    try:
        quiz_result = (
            supabase.table("quizzes")
            .select("id,title,game_mode,join_code")
            .eq("id", quiz_id)
            .eq("host_id", session["user_id"])
            .execute()
        )

        if not quiz_result.data:
            return jsonify({"error": "Quiz not found."}), 404

        quiz = quiz_result.data[0]

        question_check = (
            supabase.table("questions")
            .select("id")
            .eq("quiz_id", quiz_id)
            .limit(1)
            .execute()
        )

        if not question_check.data:
            return jsonify({
                "error": "This quiz has no questions."
            }), 400

        code = quiz.get("join_code")

        if not code:
            code = generate_join_code()

            supabase.table("quizzes").update({
                "join_code": code
            }).eq("id", quiz["id"]).execute()

        # Reuse the open lobby/game if this host already opened one.
        existing = get_game(code)

        if (
            existing
            and existing["host_id"] == session["user_id"]
            and existing["status"] in ("lobby", "active")
        ):
            return jsonify({"success": True, "code": code}), 200

        supabase.table("games").insert({
            "code": code,
            "quiz_id": str(quiz["id"]),
            "quiz_title": quiz["title"],
            "game_mode": quiz.get("game_mode") or "classic",
            "host_id": session["user_id"],
            "status": "lobby",
            "current_index": -1
        }).execute()

        return jsonify({"success": True, "code": code}), 201

    except Exception:
        app.logger.exception("Host game failed")
        return jsonify({
            "error": (
                "Could not create the game. Make sure the games, "
                "players and answers tables exist in Supabase."
            )
        }), 500


@app.route("/host/<code>")
def host_page(code):

    if not session.get("user_id"):
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    return HOST_PAGE


@app.route("/api/host/<code>/state")
def api_host_state(code):

    game, error = host_game_or_error(code)

    if error:
        return error

    try:
        return jsonify(build_state(game)), 200
    except Exception:
        app.logger.exception("Host state failed")
        return jsonify({"error": "Could not load the game."}), 500


@app.route("/api/host/<code>/start", methods=["POST"])
def api_host_start(code):

    game, error = host_game_or_error(code)

    if error:
        return error

    try:
        if game["status"] != "lobby":
            return jsonify({"error": "Game already started."}), 400

        if not load_questions(game):
            return jsonify({"error": "This quiz has no questions."}), 400

        supabase.table("games").update({
            "status": "active",
            "current_index": 0,
            "question_started_ms": now_ms()
        }).eq("id", game["id"]).execute()

        return jsonify({"success": True}), 200

    except Exception:
        app.logger.exception("Start game failed")
        return jsonify({"error": "Could not start the game."}), 500


@app.route("/api/host/<code>/next", methods=["POST"])
def api_host_next(code):

    game, error = host_game_or_error(code)

    if error:
        return error

    try:
        if game["status"] != "active":
            return jsonify({"error": "Game is not active."}), 400

        total = len(load_questions(game))
        next_index = game["current_index"] + 1

        if next_index >= total:
            supabase.table("games").update({
                "status": "finished"
            }).eq("id", game["id"]).execute()
        else:
            supabase.table("games").update({
                "current_index": next_index,
                "question_started_ms": now_ms()
            }).eq("id", game["id"]).execute()

        return jsonify({"success": True}), 200

    except Exception:
        app.logger.exception("Next question failed")
        return jsonify({"error": "Could not move to the next question."}), 500


# ==========================================
# JOIN GAME + PLAY (PLAYERS)
# ==========================================

@app.route("/join-game")
def join_game():
    return JOIN_PAGE


@app.route("/api/game-info")
def api_game_info():

    try:
        game = get_game(request.args.get("code", ""))

        if not game:
            return jsonify({"found": False}), 200

        return jsonify({
            "found": True,
            "mode": game.get("game_mode"),
            "status": game["status"]
        }), 200

    except Exception:
        app.logger.exception("Game info failed")
        return jsonify({"found": False}), 200


@app.route("/api/join", methods=["POST"])
def api_join():

    data = request.get_json(silent=True) or {}

    code = str(data.get("code", "")).strip()
    name = str(data.get("name", "")).strip()[:20]
    animal = str(data.get("animal", "🦁")).strip()[:8] or "🦁"
    team = str(data.get("team", "")).strip().lower()

    if not code or not name:
        return jsonify({
            "error": "Please enter the game code and your name."
        }), 400

    try:
        game = get_game(code)

        if not game:
            quiz_check = (
                supabase.table("quizzes")
                .select("id")
                .eq("join_code", code)
                .limit(1)
                .execute()
            )

            if quiz_check.data:
                return jsonify({
                    "error": (
                        "This quiz is not open yet. Ask the host to "
                        "press Host Game in My Quizzes first."
                    )
                }), 404

            return jsonify({"error": "Game code not found."}), 404

        if game["status"] == "finished":
            return jsonify({"error": "This game is not open yet. Ask the host to press Host Game."}), 400

        is_team = game.get("game_mode") == "team"

        if is_team and team not in TEAMS:
            return jsonify({
                "error": "Please choose a team.",
                "need_team": True
            }), 400

        taken = (
            supabase.table("players")
            .select("id")
            .eq("game_id", game["id"])
            .eq("name", name)
            .execute()
        )

        if taken.data:
            return jsonify({
                "error": "That name is already taken. Try another one."
            }), 409

        player_row = {
            "game_id": game["id"],
            "name": name,
            "animal": animal,
            "score": 0
        }

        if is_team:
            player_row["team"] = team

        created = supabase.table("players").insert(player_row).execute()

        player = created.data[0]

        session["player_id"] = str(player["id"])
        session["player_game_id"] = str(game["id"])

        return jsonify({"success": True}), 201

    except Exception:
        app.logger.exception("Join game failed")
        return jsonify({"error": "Could not join the game."}), 500


@app.route("/play")
def play():

    if not session.get("player_id") or not session.get("player_game_id"):
        return redirect(url_for("join_game"))

    return PLAY_PAGE


@app.route("/api/play/state")
def api_play_state():

    player_id = session.get("player_id")
    game_id = session.get("player_game_id")

    if not player_id or not game_id:
        return jsonify({"error": "Not in a game."}), 401

    try:
        game = get_game_by_id(game_id)

        if not game:
            return jsonify({"error": "Game not found."}), 404

        state = build_state(game, player_id)

        if "me" not in state:
            return jsonify({"error": "Player not found."}), 404

        return jsonify(state), 200

    except Exception:
        app.logger.exception("Play state failed")
        return jsonify({"error": "Could not load the game."}), 500


@app.route("/api/play/answer", methods=["POST"])
def api_play_answer():

    player_id = session.get("player_id")
    game_id = session.get("player_game_id")

    if not player_id or not game_id:
        return jsonify({"error": "Not in a game."}), 401

    try:
        game = get_game_by_id(game_id)

        if not game or game["status"] != "active":
            return jsonify({"error": "No active question."}), 400

        questions = load_questions(game)
        index = game["current_index"]

        if not 0 <= index < len(questions):
            return jsonify({"error": "No active question."}), 400

        q = questions[index]

        started = int(game.get("question_started_ms") or now_ms())
        elapsed = (now_ms() - started) / 1000

        if elapsed > q["timer"] + 1.5:
            return jsonify({"error": "Time is up!"}), 400

        data = request.get_json(silent=True) or {}
        answer = str(data.get("answer", "")).strip()

        if not answer:
            return jsonify({"error": "Please enter an answer."}), 400

        is_correct = (
            answer.casefold() == q["correct"].strip().casefold()
        )

        points = 0

        if is_correct:
            if game.get("game_mode") == "accuracy":
                points = 1000
            else:
                ratio = max(0.0, 1 - elapsed / q["timer"])
                points = int(500 + 500 * ratio)

        try:
            supabase.table("answers").insert({
                "game_id": game["id"],
                "player_id": player_id,
                "question_index": index,
                "answer": answer[:200],
                "is_correct": is_correct,
                "points": points
            }).execute()
        except Exception:
            return jsonify({"error": "You already answered."}), 409

        if points:
            current = (
                supabase.table("players")
                .select("score")
                .eq("id", player_id)
                .execute()
            )

            score = current.data[0]["score"] if current.data else 0

            supabase.table("players").update({
                "score": score + points
            }).eq("id", player_id).execute()

        return jsonify({"success": True}), 200

    except Exception:
        app.logger.exception("Answer failed")
        return jsonify({"error": "Could not send your answer."}), 500


# ==========================================
# LEADERBOARD
# ==========================================

@app.route("/leaderboard")
def leaderboard():
    return LEADERBOARD_PAGE


@app.route("/api/leaderboard")
def api_leaderboard():

    try:
        code = request.args.get("code", "").strip()
        game = None

        if code:
            game = get_game(code)
        elif session.get("user_id"):
            result = (
                supabase.table("games")
                .select("*")
                .eq("host_id", session["user_id"])
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            game = result.data[0] if result.data else None

        if not game and session.get("player_game_id"):
            game = get_game_by_id(session["player_game_id"])

        if not game:
            return jsonify({
                "error": (
                    "No game found yet. Play a game first, or open "
                    "/leaderboard?code=YOUR-GAME-CODE."
                )
            }), 404

        players = (
            supabase.table("players")
            .select("name,animal,score,team")
            .eq("game_id", game["id"])
            .order("score", desc=True)
            .order("joined_at")
            .execute()
            .data
            or []
        )

        teams = compute_teams(game, players)

        return jsonify({
            "title": game.get("quiz_title") or "Quiz",
            "code": game["code"],
            "status": game["status"],
            "game_mode": game.get("game_mode"),
            "teams": teams,
            "players": players
        }), 200

    except Exception:
        app.logger.exception("Leaderboard failed")
        return jsonify({"error": "Could not load the leaderboard."}), 500


# ==========================================
# REPORTS
# ==========================================

@app.route("/reports")
def reports():

    if not session.get("user_id"):
        return redirect(url_for("login"))

    return render_template("reports.html")


# ==========================================
# ANIMALS
# ==========================================

@app.route("/animals")
def animals():
    return render_template("animals.html")


# ==========================================
# CREATE QUIZ API
# ==========================================

@app.route("/api/create-quiz", methods=["POST"])
def api_create_quiz():

    if not session.get("user_id"):
        return jsonify({
            "error": "Please log in before creating a quiz."
        }), 401

    quiz_id = None

    try:
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({
                "error": "Invalid request data."
            }), 400

        title = str(data.get("title", "")).strip()
        game_mode = str(
            data.get("game_mode", "classic")
        ).strip()

        questions = data.get("questions", [])

        if not title:
            return jsonify({
                "error": "Please enter a quiz title."
            }), 400

        if game_mode not in ("classic", "team", "accuracy"):
            return jsonify({
                "error": "Invalid game mode."
            }), 400

        if not isinstance(questions, list) or not questions:
            return jsonify({
                "error": "Please add at least one question."
            }), 400

        question_rows = []

        allowed_types = {
            "multiple_choice",
            "true_false",
            "jumbled",
            "type_answer"
        }

        for index, item in enumerate(questions, start=1):

            if not isinstance(item, dict):
                raise ValueError(
                    f"Question {index} has invalid data."
                )

            question_text = str(
                item.get("question_text", "")
            ).strip()

            question_type = str(
                item.get("question_type", "")
            ).strip()

            correct_answer = str(
                item.get("correct_answer", "")
            ).strip()

            if not question_text or not correct_answer:
                raise ValueError(
                    f"Question {index} needs a question "
                    "and a correct answer."
                )

            if question_type not in allowed_types:
                raise ValueError(
                    f"Question {index} has an invalid type."
                )

            try:
                timer = int(item.get("timer", 30))
            except (ValueError, TypeError):
                timer = 30

            timer = max(5, min(timer, 300))

            choices = {
                "A": str(item.get("option_a", "")).strip(),
                "B": str(item.get("option_b", "")).strip(),
                "C": str(item.get("option_c", "")).strip(),
                "D": str(item.get("option_d", "")).strip(),
                "timer": timer
            }

            if question_type == "multiple_choice":

                options = [
                    choices["A"],
                    choices["B"],
                    choices["C"],
                    choices["D"]
                ]

                if not all(options):
                    raise ValueError(
                        f"Question {index} needs all four choices."
                    )

                if correct_answer.casefold() not in [
                    option.casefold() for option in options
                ]:
                    raise ValueError(
                        f"Question {index}: the correct answer "
                        "must match one of the choices."
                    )

            elif question_type == "true_false":

                if correct_answer.casefold() not in {
                    "true", "false"
                }:
                    raise ValueError(
                        f"Question {index}: answer must be True or False."
                    )

                correct_answer = (
                    "True"
                    if correct_answer.casefold() == "true"
                    else "False"
                )

                choices = {
                    "A": "True",
                    "B": "False",
                    "timer": timer
                }

            question_rows.append({
                "question": question_text,
                "question_type": question_type,
                "correct_answer": correct_answer,
                "choices": choices
            })

        # Use the code shown on the Create Quiz page.
        join_code = session.get("pending_join_code")

        if not join_code or join_code_taken(join_code):
            join_code = generate_join_code()

        # Save quiz (linked to the logged-in user via host_id).
        quiz_result = (
            supabase.table("quizzes")
            .insert({
                "title": title,
                "description": "",
                "game_mode": game_mode,
                "host_id": session["user_id"],
                "join_code": join_code
            })
            .execute()
        )

        if not quiz_result.data:
            raise RuntimeError("Quiz was not returned after insertion.")

        quiz_id = quiz_result.data[0]["id"]
        session.pop("pending_join_code", None)

        # Link every question to its quiz.
        for row in question_rows:
            row["quiz_id"] = quiz_id

        # Save all questions.
        supabase.table("questions").insert(
            question_rows
        ).execute()

        return jsonify({
            "success": True,
            "message": "Quiz created successfully!",
            "quiz_id": quiz_id,
            "join_code": join_code
        }), 201

    except ValueError as error:

        if quiz_id is not None:
            try:
                supabase.table("quizzes").delete().eq(
                    "id", quiz_id
                ).execute()
            except Exception:
                app.logger.exception("Quiz cleanup failed")

        return jsonify({
            "error": str(error)
        }), 400

    except Exception:

        app.logger.exception("Create quiz failed")

        if quiz_id is not None:
            try:
                supabase.table("quizzes").delete().eq(
                    "id", quiz_id
                ).execute()
            except Exception:
                app.logger.exception("Quiz cleanup failed")

        return jsonify({
            "error": (
                "Could not save the quiz. "
                "Check the Render logs for the detailed error."
            )
        }), 500


# ==========================================
# HEALTH CHECK
# ==========================================

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "app": "QuizUp"
    }), 200


# ==========================================
# RUN LOCAL SERVER
# ==========================================

if __name__ == "__main__":
    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )
