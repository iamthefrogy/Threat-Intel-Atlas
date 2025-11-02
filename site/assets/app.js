const items = Array.isArray(window.__ATLAS_ITEMS__) ? window.__ATLAS_ITEMS__ : [];
const feedList = document.getElementById('feed-list');
const searchInput = document.getElementById('search');
const clearFilters = document.getElementById('clear-filters');
const hotTags = document.getElementById('hot-tags');

let activeTag = null;
let searchTerm = '';

const formatDate = (iso) => {
  try {
    const date = new Date(iso);
    return `${date.toISOString().slice(0, 16).replace('T', ' ')} UTC`;
  } catch (err) {
    return iso;
  }
};

const createTagPill = (tag) => {
  const pill = document.createElement('button');
  pill.className = 'tag-pill';
  pill.type = 'button';
  pill.dataset.tag = tag;
  pill.textContent = tag;
  pill.addEventListener('click', () => {
    activeTag = activeTag === tag ? null : tag;
    render();
  });
  return pill;
};

const render = () => {
  feedList.innerHTML = '';
  const filtered = items.filter((item) => {
    const haystack = `${item.title} ${item.summary} ${item.source}`.toLowerCase();
    const matchesSearch = searchTerm ? haystack.includes(searchTerm) : true;
    const matchesTag = activeTag ? item.tags.includes(activeTag) : true;
    return matchesSearch && matchesTag;
  });

  if (!filtered.length) {
    const empty = document.createElement('p');
    empty.textContent = 'No signals match the current filter.';
    empty.style.color = 'var(--muted)';
    feedList.appendChild(empty);
    return;
  }

  filtered.forEach((item) => {
    const card = document.createElement('article');
    card.className = 'feed-card';

    const title = document.createElement('a');
    title.href = item.link;
    title.textContent = item.title;
    title.target = '_blank';
    title.rel = 'noopener noreferrer';
    card.appendChild(title);

    const meta = document.createElement('div');
    meta.className = 'feed-meta';
    meta.innerHTML = `
      <span>Source: ${item.source}</span>
      <span>Published: ${formatDate(item.published)}</span>
      <span>Tags: ${item.tags.length ? item.tags.join(', ') : 'unclassified'}</span>
    `;
    card.appendChild(meta);

    if (item.summary) {
      const summary = document.createElement('p');
      summary.className = 'feed-summary';
      summary.textContent = item.summary;
      card.appendChild(summary);
    }

    if (item.tags.length) {
      const tagsWrap = document.createElement('div');
      tagsWrap.className = 'feed-meta';
      item.tags.forEach((tag) => {
        tagsWrap.appendChild(createTagPill(tag));
      });
      card.appendChild(tagsWrap);
    }

    feedList.appendChild(card);
  });
};

if (searchInput) {
  searchInput.addEventListener('input', (event) => {
    searchTerm = event.currentTarget.value.trim().toLowerCase();
    render();
  });
}

if (clearFilters) {
  clearFilters.addEventListener('click', () => {
    activeTag = null;
    searchTerm = '';
    if (searchInput) {
      searchInput.value = '';
    }
    render();
  });
}

if (hotTags) {
  hotTags.querySelectorAll('li[data-tag]').forEach((node) => {
    node.style.cursor = 'pointer';
    node.addEventListener('click', () => {
      const tag = node.dataset.tag;
      activeTag = activeTag === tag ? null : tag;
      render();
    });
  });
}

render();
