"use strict";
document.documentElement.classList.add("js");

const menu = document.querySelector(".menu-button");
const nav = document.querySelector(".main-nav");
if (menu && nav) {
  menu.hidden = false;
  menu.addEventListener("click", () => {
    const opened = nav.classList.toggle("is-open");
    menu.setAttribute("aria-expanded", String(opened));
    menu.querySelector("span").textContent = opened ? "−" : "＋";
  });
}

const groups = [...document.querySelectorAll(".nav-group")];
groups.forEach(group => group.addEventListener("toggle", () => {
  if (group.open) groups.forEach(other => { if (other !== group) other.open = false; });
}));
document.addEventListener("click", event => {
  groups.forEach(group => { if (!group.contains(event.target)) group.open = false; });
});
document.addEventListener("keydown", event => {
  if (event.key !== "Escape") return;
  const current = groups.find(group => group.open);
  if (current) {
    current.open = false;
    current.querySelector("summary").focus();
  } else if (nav?.classList.contains("is-open")) {
    nav.classList.remove("is-open");
    menu.setAttribute("aria-expanded", "false");
    menu.querySelector("span").textContent = "＋";
    menu.focus();
  }
});

const progress = document.querySelector(".reading-progress span");
if (progress) {
  const update = () => {
    const article = document.querySelector(".prose");
    const top = article.getBoundingClientRect().top + window.scrollY;
    const distance = Math.max(1, article.offsetHeight - window.innerHeight * 0.6);
    progress.style.width = `${Math.min(100, Math.max(0, (window.scrollY - top) / distance * 100))}%`;
  };
  window.addEventListener("scroll", update, {passive: true});
  window.addEventListener("resize", update);
  window.addEventListener("load", update);
  update();
}

const form = document.querySelector(".search-form");
if (form) initializeSearch();

async function initializeSearch() {
  const input = document.querySelector("#query");
  const filter = document.querySelector("#category-filter");
  const results = document.querySelector("#search-results");
  const status = document.querySelector("#search-status");
  const empty = document.querySelector("#search-empty");
  try {
    const response = await fetch(form.dataset.index);
    if (!response.ok) throw new Error("Search index unavailable");
    const items = await response.json();
    const params = new URLSearchParams(location.search);
    input.value = params.get("q") || "";
    filter.value = params.get("category") || "";
    const normalize = value => value.normalize("NFKC").toLocaleLowerCase().trim();
    // Create DOM nodes instead of interpolating content or search queries into HTML.
    function render() {
      const tokens = normalize(input.value).split(/\s+/).filter(Boolean);
      const matching = items.filter(item => (!filter.value || item.category === filter.value)
        && tokens.every(token => normalize(`${item.text} ${item.category_title}`).includes(token)));
      results.replaceChildren();
      matching.forEach(item => {
        const card = document.createElement("article");
        card.className = "story-card";
        const a = document.createElement("a");
        a.href = item.url;
        const imageBox = document.createElement("div");
        imageBox.className = "card-image";
        const image = document.createElement("img");
        Object.assign(image, {src: item.image, alt: item.alt, loading: "lazy", width: 1536, height: 1024});
        imageBox.append(image);
        const copy = document.createElement("div");
        copy.className = "card-copy";
        const category = document.createElement("p");
        category.className = "eyebrow";
        category.textContent = `${item.category_title} / ${item.subcategory}`;
        const title = document.createElement("h2");
        title.textContent = item.title;
        const summary = document.createElement("p");
        summary.textContent = item.summary;
        const read = document.createElement("span");
        read.className = "text-link";
        read.textContent = "이야기 읽기 ↗";
        copy.append(category, title, summary, read);
        a.append(imageBox, copy);
        card.append(a);
        results.append(card);
      });
      status.textContent = tokens.length || filter.value ? `${matching.length}개의 이야기를 찾았습니다` : `전체 ${matching.length}개의 이야기`;
      empty.hidden = matching.length !== 0;
      const next = new URL(location.href);
      if (input.value.trim()) next.searchParams.set("q", input.value.trim()); else next.searchParams.delete("q");
      if (filter.value) next.searchParams.set("category", filter.value); else next.searchParams.delete("category");
      history.replaceState(null, "", next);
    }
    form.addEventListener("submit", event => { event.preventDefault(); render(); });
    input.addEventListener("input", render);
    filter.addEventListener("change", render);
    document.querySelector("#reset-search").addEventListener("click", () => {
      input.value = ""; filter.value = ""; render(); input.focus();
    });
    render();
  } catch (error) {
    status.textContent = "검색을 불러오지 못했습니다. 아래 이야기 목록을 이용해 주세요.";
    form.querySelector("button").disabled = true;
    input.disabled = true;
    filter.disabled = true;
  }
}
