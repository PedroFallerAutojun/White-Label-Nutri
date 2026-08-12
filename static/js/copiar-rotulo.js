// Copia o rótulo preservando a formatação para colar no Google Docs.
// Usa a Clipboard API (text/html) com fallback para execCommand nos navegadores
// que ainda não a suportam — o original só tinha o execCommand (deprecated).
(function () {
  "use strict";

  const LARGURA_LUPA = 140; // px — tamanho esperado da lupa no documento final

  function ajustarLupas(raiz) {
    const originais = [];
    raiz.querySelectorAll(".imagem-lupa-copia").forEach(function (img) {
      const larguraNatural = img.naturalWidth || img.width;
      const alturaNatural = img.naturalHeight || img.height;
      const estilo = img.getAttribute("style") || "";
      let altura = alturaNatural;
      if (larguraNatural > 0) {
        altura = Math.round(LARGURA_LUPA * (alturaNatural / larguraNatural));
      }
      img.setAttribute("width", LARGURA_LUPA);
      img.setAttribute("height", altura);
      img.style.cssText = estilo + "; width: " + LARGURA_LUPA + "px; height: " + altura + "px;";
      originais.push({ img: img, estilo: estilo });
    });
    return function reverter() {
      originais.forEach(function (item) {
        item.img.removeAttribute("width");
        item.img.removeAttribute("height");
        if (item.estilo) {
          item.img.setAttribute("style", item.estilo);
        } else {
          item.img.removeAttribute("style");
        }
      });
    };
  }

  function copiarSelecao(elemento) {
    const range = document.createRange();
    range.selectNode(elemento);
    const selecao = window.getSelection();
    selecao.removeAllRanges();
    selecao.addRange(range);
    let ok = false;
    try {
      ok = document.execCommand("copy");
    } catch (erro) {
      ok = false;
    }
    selecao.removeAllRanges();
    return ok;
  }

  async function copiar(elemento) {
    if (navigator.clipboard && window.ClipboardItem) {
      try {
        await navigator.clipboard.write([
          new ClipboardItem({
            "text/html": new Blob([elemento.innerHTML], { type: "text/html" }),
            "text/plain": new Blob([elemento.innerText], { type: "text/plain" }),
          }),
        ]);
        return true;
      } catch (erro) {
        // cai no fallback
      }
    }
    return copiarSelecao(elemento);
  }

  document.addEventListener("DOMContentLoaded", function () {
    const botao = document.querySelector("[data-rotulo-copiar]");
    const conteudo = document.getElementById("conteudo-para-copiar");
    if (!botao || !conteudo) return;

    botao.addEventListener("click", async function () {
      const reverter = ajustarLupas(conteudo);
      const textoOriginal = botao.textContent;
      const ok = await copiar(conteudo);
      reverter();
      botao.textContent = ok ? "Copiado!" : "Falha ao copiar";
      botao.disabled = true;
      setTimeout(function () {
        botao.textContent = textoOriginal;
        botao.disabled = false;
      }, 2000);
    });
  });
})();
