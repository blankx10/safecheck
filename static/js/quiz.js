var questions = [];
var currentIndex = 0;
var answers = [];

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function showQuestion() {
  var root = document.getElementById("quiz-root");
  document.getElementById("quiz-result").classList.add("hidden");
  document.getElementById("quiz-restart").classList.add("hidden");
  if (currentIndex >= questions.length) {
    showSummary();
    return;
  }
  var item = questions[currentIndex];
  var options = item.options.map(function (option, index) {
    return '<button type="button" class="block w-full text-left border rounded-xl px-4 py-3 hover:bg-blue-50" data-index="' +
      index + '">' + escapeHtml(option) + "</button>";
  }).join("");
  root.innerHTML =
    "<p class='text-sm text-slate-500'>第 " + (currentIndex + 1) + " / " + questions.length + " 题 · " + escapeHtml(item.category) + "</p>" +
    "<h2 class='text-lg font-semibold mt-2'>" + escapeHtml(item.question) + "</h2>" +
    "<div class='mt-4 space-y-2' id='option-list'>" + options + "</div>" +
    "<div id='explain-box' class='mt-4 hidden'></div>";
}

function showSummary() {
  var root = document.getElementById("quiz-root");
  var correctCount = answers.filter(function (item) { return item.is_correct; }).length;
  var percent = questions.length ? Math.round((correctCount / questions.length) * 100) : 0;
  var wrong = answers.filter(function (item) { return !item.is_correct; });
  var wrongHtml = wrong.length
    ? "<ul class='space-y-3'>" + wrong.map(function (item) {
      return "<li class='border rounded-xl p-3'><p class='font-medium'>" + escapeHtml(item.question) + "</p>" +
        "<p class='text-sm text-red-700'>你的选择：" + escapeHtml(item.chosen) + "</p>" +
        "<p class='text-sm text-green-700'>较稳妥的做法：" + escapeHtml(item.correct) + "</p>" +
        "<p class='text-sm text-slate-600'>" + escapeHtml(item.explanation) + "</p></li>";
    }).join("") + "</ul>"
    : "<p class='text-green-700'>全部答对了。请继续保持警惕，安全没有绝对保证。</p>";
  root.innerHTML = "";
  var result = document.getElementById("quiz-result");
  result.classList.remove("hidden");
  result.innerHTML =
    "<article class='rounded-2xl bg-white p-5 shadow space-y-3'><h2 class='text-xl font-semibold'>得分：" +
    correctCount + " / " + questions.length + "（正确率 " + percent + "%）</h2>" + wrongHtml + "</article>";
  document.getElementById("quiz-restart").classList.remove("hidden");
}

async function startQuiz() {
  currentIndex = 0;
  answers = [];
  var response = await fetch("/api/quiz");
  var data = await response.json();
  questions = data.questions || [];
  showQuestion();
}

document.addEventListener("DOMContentLoaded", function () {
  startQuiz();
  document.getElementById("quiz-root").addEventListener("click", async function (event) {
    var button = event.target.closest("[data-index]");
    if (!button || button.disabled) {
      return;
    }
    var chosen = Number(button.getAttribute("data-index"));
    var item = questions[currentIndex];
    Array.prototype.forEach.call(document.querySelectorAll("#option-list button"), function (node) {
      node.disabled = true;
    });
    var response = await fetch("/api/quiz/answer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: window.safecheckSessionId,
        scenario_id: item.id,
        chosen_index: chosen,
      }),
    });
    var data = await response.json();
    var explain = document.getElementById("explain-box");
    explain.classList.remove("hidden");
    explain.innerHTML =
      "<p class='" + (data.is_correct ? "text-green-700" : "text-red-700") + "'>" +
      (data.is_correct ? "选择合理。" : "这个选择风险较高。") + "</p>" +
      "<p class='text-sm text-slate-600 mt-1'>" + escapeHtml(data.explanation) + "</p>" +
      "<button type='button' id='next-question' class='mt-3 bg-blue-700 text-white rounded-xl px-4 py-2 hover:bg-blue-800'>下一题</button>";
    answers.push({
      question: item.question,
      chosen: item.options[chosen],
      correct: item.options[data.correct_index],
      explanation: data.explanation,
      is_correct: data.is_correct,
    });
    document.getElementById("next-question").addEventListener("click", function () {
      currentIndex += 1;
      showQuestion();
    });
  });
  document.getElementById("quiz-restart").addEventListener("click", startQuiz);
});
