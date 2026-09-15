function toHex(buffer) {
  return Array.from(new Uint8Array(buffer))
    .map(function (byte) {
      return byte.toString(16).padStart(2, "0");
    })
    .join("")
    .toUpperCase();
}

function showError(message) {
  var box = document.getElementById("password-error");
  box.textContent = message;
  box.classList.remove("hidden");
}

async function checkPassword(password) {
  var data = new TextEncoder().encode(password);
  var digest = await crypto.subtle.digest("SHA-1", data);
  var hash = toHex(digest);
  var prefix = hash.slice(0, 5);
  var suffix = hash.slice(5);
  var response = await fetch("/api/hibp/" + prefix);
  if (!response.ok) {
    throw new Error("泄露库暂时不可用");
  }
  var text = await response.text();
  var count = 0;
  text.split("\n").forEach(function (line) {
    var parts = line.trim().split(":");
    if (parts[0] && parts[0].toUpperCase() === suffix) {
      count = parseInt(parts[1], 10) || 0;
    }
  });
  var strength = window.zxcvbn ? zxcvbn(password) : { score: 0, feedback: {} };
  return { count: count, strength: strength };
}

function renderResult(count, strength) {
  var leaked = count > 0;
  var suggestions = (strength.feedback && strength.feedback.suggestions) || [];
  var extra = ["使用密码管理器", "开启两步验证", "不要重复使用密码", "长度至少 12 位"];
  var items = suggestions.concat(extra).map(function (tip) {
    return "<li>" + tip + "</li>";
  }).join("");
  document.getElementById("password-result").innerHTML =
    '<div class="rounded-2xl p-5 border ' + (leaked ? "bg-red-50 border-red-200 text-red-800" : "bg-green-50 border-green-200 text-green-800") + '">' +
    "<p class='font-semibold'>" + (leaked
      ? "该密码已在数据泄露中出现 " + count + " 次，请立即停止使用。"
      : "未在已知泄露库中找到，但不代表绝对安全。") + "</p>" +
    "<p class='mt-2'>强度评分（0–4）：" + strength.score + "</p>" +
    "<p class='mt-1'>" + ((strength.feedback && strength.feedback.warning) || "") + "</p>" +
    "<ul class='list-disc pl-5 mt-2 text-slate-800'>" + items + "</ul>" +
    "</div>";
}

document.addEventListener("DOMContentLoaded", function () {
  var form = document.getElementById("password-form");
  var toggle = document.getElementById("toggle-password");
  var input = document.getElementById("password-input");

  toggle.addEventListener("click", function () {
    var hidden = input.type === "password";
    input.type = hidden ? "text" : "password";
    toggle.textContent = hidden ? "隐藏" : "显示";
  });

  form.addEventListener("submit", async function (event) {
    event.preventDefault();
    document.getElementById("password-error").classList.add("hidden");
    var password = input.value;
    if (!password) {
      showError("请先输入密码。密码不会离开浏览器。");
      return;
    }
    try {
      var result = await checkPassword(password);
      renderResult(result.count, result.strength);
      fetch("/api/password-check-count", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: window.safecheckSessionId }),
      });
    } catch (error) {
      showError("检查失败，请稍后再试。若持续失败，可能是服务暂时不可用。");
    }
  });
});
