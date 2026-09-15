var priorityRank = { 高: 0, 中: 1, 低: 2 };
var checklistData = null;
var checklistFilter = "all";

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function updateProgress(progress) {
  var total = progress.total || 0;
  var completed = progress.completed || 0;
  var percent = total ? Math.round((completed / total) * 100) : 0;
  document.getElementById("progress-label").textContent = completed + " / " + total;
  document.getElementById("progress-bar").style.width = percent + "%";
  document.getElementById("progress-bar-wrap").setAttribute("aria-valuenow", String(percent));
}

function renderChecklist(data) {
  checklistData = data;
  var root = document.getElementById("checklist-root");
  var visibleCategories = data.categories.map(function (category) {
    return {
      name: category.name,
      items: category.items.filter(function (item) {
        return checklistFilter === "all" ||
          (checklistFilter === "todo" && !item.completed) ||
          (checklistFilter === "high" && item.priority === "高");
      }),
    };
  }).filter(function (category) { return category.items.length; });
  root.innerHTML = visibleCategories.map(function (category) {
    var done = category.items.filter(function (item) { return item.completed; }).length;
    var itemsHtml = category.items.map(function (item) {
      return (
        '<label class="flex gap-3 items-start p-3 rounded-xl hover:bg-slate-50">' +
        '<input type="checkbox" class="mt-1" data-item-id="' + item.id + '" ' +
        (item.completed ? "checked" : "") + ' aria-label="' + escapeHtml(item.title) + '">' +
        "<span><span class='font-medium'>" + escapeHtml(item.title) + "</span>" +
        "<span class='ml-2 text-xs px-2 py-0.5 rounded " +
        (item.priority === "高" ? "bg-red-100 text-red-800" : item.priority === "中" ? "bg-yellow-100 text-yellow-800" : "bg-green-100 text-green-800") +
        "'>" + escapeHtml(item.priority) + "</span>" +
        "<span class='block text-sm text-slate-600'>" + escapeHtml(item.description) + "</span></span></label>"
      );
    }).join("");
    return (
      '<section class="bg-white rounded-2xl p-5 shadow"><h2 class="font-semibold mb-2">' +
      escapeHtml(category.name) + "（" + done + "/" + category.items.length + "）</h2>" + itemsHtml + "</section>"
    );
  }).join("") || '<p class="bg-white rounded-2xl p-5 text-slate-600">当前筛选下没有项目。</p>';
  updateProgress(data.progress);
}

async function loadChecklist() {
  var response = await fetch("/api/checklist?session_id=" + encodeURIComponent(window.safecheckSessionId));
  if (!response.ok) {
    throw new Error("清单加载失败");
  }
  var data = await response.json();
  renderChecklist(data);
}

function setStatus(message, isError) {
  var status = document.getElementById("checklist-status");
  status.textContent = message;
  status.className = "text-sm " + (isError ? "text-red-700" : "text-slate-500");
}

document.addEventListener("DOMContentLoaded", function () {
  loadChecklist().catch(function () { setStatus("清单加载失败，请刷新重试。", true); });

  document.getElementById("checklist-filter").addEventListener("change", function (event) {
    checklistFilter = event.target.value;
    renderChecklist(checklistData);
  });

  document.getElementById("checklist-root").addEventListener("change", async function (event) {
    var checkbox = event.target;
    if (checkbox.tagName !== "INPUT") {
      return;
    }
    var itemId = Number(checkbox.getAttribute("data-item-id"));
    var completed = checkbox.checked;
    checkbox.disabled = true;
    setStatus("正在保存…", false);
    try {
      var response = await fetch("/api/checklist/toggle", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: window.safecheckSessionId,
          item_id: itemId,
          completed: completed,
        }),
      });
      if (!response.ok) {
        throw new Error("保存失败");
      }
      checklistData.categories.forEach(function (category) {
        category.items.forEach(function (item) {
          if (item.id === itemId) {
            item.completed = completed;
          }
        });
      });
      checklistData.progress.completed += completed ? 1 : -1;
      renderChecklist(checklistData);
      setStatus("已保存", false);
    } catch (error) {
      checkbox.checked = !completed;
      setStatus("保存失败，请重试。", true);
    } finally {
      checkbox.disabled = false;
    }
  });

  document.getElementById("plan-button").addEventListener("click", function () {
    if (!checklistData) {
      return;
    }
    var unfinished = [];
    checklistData.categories.forEach(function (category) {
      category.items.forEach(function (item) {
        if (!item.completed) {
          unfinished.push({ category: category.name, item: item });
        }
      });
    });
    unfinished.sort(function (a, b) {
      return (priorityRank[a.item.priority] || 9) - (priorityRank[b.item.priority] || 9);
    });
    var box = document.getElementById("plan-box");
    box.classList.remove("hidden");
    if (!unfinished.length) {
      box.innerHTML = "<p>清单项都已勾选。请继续保持，安全没有绝对保证。</p>";
      return;
    }
    box.innerHTML = "<h2 class='font-semibold mb-2'>建议优先完成</h2><ol class='list-decimal pl-5 space-y-2'>" +
      unfinished.map(function (row) {
        return "<li><strong>[" + escapeHtml(row.item.priority) + "] " + escapeHtml(row.category) + "</strong>：" +
          escapeHtml(row.item.title) + " — " + escapeHtml(row.item.description) + "</li>";
      }).join("") + "</ol>";
  });
});
