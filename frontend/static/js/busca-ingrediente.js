// Autocomplete de ingredientes da receita (etapa 2).
// Substitui o <datalist>, cuja busca depende do navegador e diferencia acentos:
// aqui "acucar uniao" acha "Açúcar de confeiteiro (União)" — sem acento, sem
// maiúsculas, palavras em qualquer ordem, no nome ou na marca.
(function () {
  "use strict";

  const MAX_SUGESTOES = 50;

  const caixa = document.querySelector("[data-busca-ingrediente]");
  if (!caixa) return;
  const campo = caixa.querySelector("#ingExtra");
  const campoId = caixa.querySelector("#ingId");
  const lista = caixa.querySelector("#sugestoesIngrediente");
  const dados = JSON.parse(document.getElementById("dadosIngredientes").textContent);

  // Normaliza caractere a caractere para poder destacar o trecho no texto original.
  function normalizarChar(c) {
    return c.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  }

  function normalizar(texto) {
    return Array.from(texto.normalize("NFC")).map(normalizarChar).join("");
  }

  function palavras(texto) {
    return normalizar(texto).split(/\s+/).filter(Boolean);
  }

  const ingredientes = dados.map(function (item) {
    const exibicao = item.marca ? item.nome + " (" + item.marca + ")" : item.nome;
    return {
      id: item.id,
      nome: item.nome,
      marca: item.marca || "",
      exibicao: exibicao,
      nomeNorm: normalizar(item.nome),
      tudoNorm: normalizar(exibicao),
    };
  });

  // Menor = melhor: começa com o que foi digitado > alguma palavra do nome começa
  // com o termo > todos os termos estão no nome > algum termo só bate na marca.
  function pontuar(item, termos, consulta) {
    if (!termos.every(function (t) { return item.tudoNorm.includes(t); })) return null;
    if (item.nomeNorm.startsWith(consulta)) return 0;
    const inicioDePalavra = item.nomeNorm.split(/[\s,/()-]+/).some(function (p) {
      return p.startsWith(termos[0]);
    });
    if (inicioDePalavra) return 1;
    if (termos.every(function (t) { return item.nomeNorm.includes(t); })) return 2;
    return 3;
  }

  function buscar(texto) {
    const termos = palavras(texto);
    if (!termos.length) return { itens: [], total: 0 };
    const consulta = termos.join(" ");
    const achados = [];
    ingredientes.forEach(function (item) {
      const nota = pontuar(item, termos, consulta);
      if (nota !== null) achados.push({ item: item, nota: nota });
    });
    achados.sort(function (a, b) {
      return a.nota - b.nota
        || a.item.nome.length - b.item.nome.length
        || a.item.exibicao.localeCompare(b.item.exibicao, "pt-BR");
    });
    return {
      itens: achados.slice(0, MAX_SUGESTOES).map(function (a) { return a.item; }),
      total: achados.length,
    };
  }

  // Monta o texto com <mark> nos trechos que bateram com algum termo.
  function destacar(texto, termos, destino) {
    const chars = Array.from(texto.normalize("NFC"));
    const norm = chars.map(normalizarChar);
    const juntos = norm.join("");
    const posicao = []; // índice no texto normalizado → índice do caractere original
    norm.forEach(function (n, i) { for (let k = 0; k < n.length; k++) posicao.push(i); });

    const marcado = new Array(chars.length).fill(false);
    termos.forEach(function (t) {
      let i = juntos.indexOf(t);
      while (i !== -1) {
        for (let k = i; k < i + t.length; k++) marcado[posicao[k]] = true;
        i = juntos.indexOf(t, i + t.length);
      }
    });

    let trecho = "";
    let emDestaque = false;
    function despejar() {
      if (!trecho) return;
      if (emDestaque) {
        const mark = document.createElement("mark");
        mark.className = "p-0";
        mark.textContent = trecho;
        destino.appendChild(mark);
      } else {
        destino.appendChild(document.createTextNode(trecho));
      }
      trecho = "";
    }
    chars.forEach(function (c, i) {
      if (marcado[i] !== emDestaque) { despejar(); emDestaque = marcado[i]; }
      trecho += c;
    });
    despejar();
  }

  let resultados = [];
  let ativo = -1;

  function fechar() {
    lista.classList.remove("show");
    campo.setAttribute("aria-expanded", "false");
    campo.removeAttribute("aria-activedescendant");
    ativo = -1;
  }

  function marcarAtivo(indice) {
    const opcoes = lista.querySelectorAll("[role=option]");
    opcoes.forEach(function (op, i) {
      const sim = i === indice;
      op.classList.toggle("active", sim);
      op.setAttribute("aria-selected", sim ? "true" : "false");
      if (sim) {
        campo.setAttribute("aria-activedescendant", op.id);
        op.scrollIntoView({ block: "nearest" });
      }
    });
    ativo = indice;
  }

  function escolher(item) {
    campo.value = item.exibicao;
    campoId.value = item.id;
    fechar();
  }

  function renderizar() {
    const texto = campo.value;
    const termos = palavras(texto);
    const busca = buscar(texto);
    resultados = busca.itens;
    lista.replaceChildren();
    if (!termos.length) { fechar(); return; }

    if (!resultados.length) {
      const vazio = document.createElement("li");
      vazio.className = "dropdown-item-text text-secondary small";
      vazio.textContent = "Nenhum ingrediente encontrado.";
      lista.appendChild(vazio);
    }
    resultados.forEach(function (item, i) {
      const li = document.createElement("li");
      const botao = document.createElement("div");
      botao.className = "dropdown-item text-wrap";
      botao.id = "sugestaoIngrediente" + i;
      botao.setAttribute("role", "option");
      destacar(item.nome, termos, botao);
      if (item.marca) {
        const marca = document.createElement("span");
        marca.className = "text-secondary";
        marca.appendChild(document.createTextNode(" ("));
        destacar(item.marca, termos, marca);
        marca.appendChild(document.createTextNode(")"));
        botao.appendChild(marca);
      }
      // mousedown (e não click) para escolher antes do blur fechar a lista
      botao.addEventListener("mousedown", function (e) {
        e.preventDefault();
        escolher(item);
      });
      li.appendChild(botao);
      lista.appendChild(li);
    });
    if (busca.total > resultados.length) {
      const mais = document.createElement("li");
      mais.className = "dropdown-item-text text-secondary small";
      mais.textContent = "Mostrando " + resultados.length + " de " + busca.total +
        " — continue digitando para refinar.";
      lista.appendChild(mais);
    }
    lista.classList.add("show");
    campo.setAttribute("aria-expanded", "true");
    marcarAtivo(resultados.length ? 0 : -1);
  }

  campo.addEventListener("input", function () {
    campoId.value = ""; // o texto mudou: a escolha anterior não vale mais
    renderizar();
  });

  campo.addEventListener("focus", function () {
    if (campo.value && !campoId.value) renderizar();
  });

  campo.addEventListener("blur", fechar);

  campo.addEventListener("keydown", function (e) {
    const aberta = lista.classList.contains("show");
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      if (!aberta) { renderizar(); return; }
      e.preventDefault();
      if (!resultados.length) return;
      const passo = e.key === "ArrowDown" ? 1 : -1;
      marcarAtivo((ativo + passo + resultados.length) % resultados.length);
    } else if (e.key === "Enter" && aberta && ativo >= 0) {
      e.preventDefault(); // escolhe a sugestão em vez de enviar o formulário
      escolher(resultados[ativo]);
    } else if (e.key === "Escape" && aberta) {
      e.preventDefault();
      fechar();
    }
  });
})();
