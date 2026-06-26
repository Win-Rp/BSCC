const titles = {
  upload: "上传查重",
  progress: "任务进度",
  results: "结果汇总",
  compare: "文档对比",
  recover: "任务恢复",
  admin: "管理后台"
};

function showScreen(id) {
  document.querySelectorAll(".screen").forEach((screen) => {
    screen.classList.toggle("active", screen.id === id);
  });
  document.querySelectorAll(".nav-item").forEach((item) => {
    item.classList.toggle("active", item.dataset.screen === id);
  });
  document.getElementById("screen-title").textContent = titles[id] || "标书查重";
}

document.querySelectorAll("[data-screen], [data-screen-jump]").forEach((node) => {
  node.addEventListener("click", () => {
    showScreen(node.dataset.screen || node.dataset.screenJump);
    document.getElementById("pay-modal").classList.remove("open");
  });
});

document.getElementById("open-pay").addEventListener("click", () => {
  document.getElementById("pay-modal").classList.add("open");
});

document.getElementById("close-pay").addEventListener("click", () => {
  document.getElementById("pay-modal").classList.remove("open");
});

document.getElementById("paid-demo").addEventListener("click", () => {
  document.getElementById("pay-modal").classList.remove("open");
  showScreen("compare");
});

document.querySelectorAll("[data-pair]").forEach((mark) => {
  mark.addEventListener("click", () => {
    document.querySelectorAll(".focused").forEach((node) => node.classList.remove("focused"));
    const target = document.getElementById(mark.dataset.pair);
    mark.classList.add("focused");
    if (target) {
      target.classList.add("focused");
      target.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  });
});
