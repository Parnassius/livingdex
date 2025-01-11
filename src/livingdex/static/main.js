function connect(timestamp) {
  const url = new URL(document.location.href);
  url.pathname = `/sse${url.pathname}/${timestamp}`;
  const sse = new EventSource(url);
  sse.addEventListener("boxes", onSseBoxes);
  sse.addEventListener("caught", onSseCaught);
}

function onSseBoxes(event) {
  const data = JSON.parse(event.data);
  const boxElements = document.querySelectorAll("main .box");
  for (const [boxId, box] of data.entries()) {
    const slotElements = boxElements[boxId].querySelectorAll(".box-content > div");
    for (const [slotId, slot] of box.entries()) {
      const el = slotElements[slotId];
      const [status, text] = slot.split("|");
      el.dataset.slotStatus = status;
      if (text) {
        el.dataset.smallText = text;
      } else {
        delete el.dataset.smallText;
      }
    }
  }
}

function onSseCaught(event) {
  const [gameId, caughtNumber, totalNumber] = event.data.split("|");
  document.querySelector(`#game-${gameId} a small`).textContent =
    `(${caughtNumber} / ${totalNumber})`;
}

const hash = new URL(import.meta.url).hash;
if (hash) {
  connect(hash.substring(1));
}
