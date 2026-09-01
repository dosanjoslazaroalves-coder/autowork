from dataclasses import dataclass, field
from typing import Dict, List

@dataclass(frozen=True)
class SiteInfo:
    """Informações de um site no catálogo."""
    nome: str
    url: str
    sinonimos: List[str] = field(default_factory=list)
    categoria: str = ""

CATALOGO_SITES: Dict[str, SiteInfo] = {
    # ── Pesquisa ──
    "google": SiteInfo(
        nome="google",
        url="https://www.google.com",
        sinonimos=["google", "googlar"],
        categoria="pesquisa",
    ),
    "bing": SiteInfo(
        nome="bing",
        url="https://www.bing.com",
        sinonimos=["bing"],
        categoria="pesquisa",
    ),
    "duckduckgo": SiteInfo(
        nome="duckduckgo",
        url="https://duckduckgo.com",
        sinonimos=["duckduckgo"],
        categoria="pesquisa",
    ),
    "yahoo": SiteInfo(
        nome="yahoo",
        url="https://www.yahoo.com",
        sinonimos=["yahoo"],
        categoria="pesquisa",
    ),
    "ecosia": SiteInfo(
        nome="ecosia",
        url="https://www.ecosia.org",
        sinonimos=["ecosia"],
        categoria="pesquisa",
    ),
    # ── Inteligência Artificial ──
    "chatgpt": SiteInfo(
        nome="chatgpt",
        url="https://chatgpt.com",
        sinonimos=["chatgpt", "chat gpt", "gpt", "openai chat"],
        categoria="inteligencia_artificial",
    ),
    "claude": SiteInfo(
        nome="claude",
        url="https://claude.ai",
        sinonimos=["claude", "claude ai", "anthropic"],
        categoria="inteligencia_artificial",
    ),
    "gemini": SiteInfo(
        nome="gemini",
        url="https://gemini.google.com",
        sinonimos=["gemini", "google gemini", "bard"],
        categoria="inteligencia_artificial",
    ),
    "copilot": SiteInfo(
        nome="copilot",
        url="https://copilot.microsoft.com",
        sinonimos=["copilot", "microsoft copilot"],
        categoria="inteligencia_artificial",
    ),
    "perplexity": SiteInfo(
        nome="perplexity",
        url="https://www.perplexity.ai",
        sinonimos=["perplexity", "perplexity ai"],
        categoria="inteligencia_artificial",
    ),
    "poe": SiteInfo(
        nome="poe",
        url="https://poe.com",
        sinonimos=["poe"],
        categoria="inteligencia_artificial",
    ),
    "huggingface": SiteInfo(
        nome="huggingface",
        url="https://huggingface.co",
        sinonimos=["huggingface", "hugging face", "hf"],
        categoria="inteligencia_artificial",
    ),
    "ollama": SiteInfo(
        nome="ollama",
        url="https://ollama.ai",
        sinonimos=["ollama"],
        categoria="inteligencia_artificial",
    ),
    "openrouter": SiteInfo(
        nome="openrouter",
        url="https://openrouter.ai",
        sinonimos=["openrouter", "open router"],
        categoria="inteligencia_artificial",
    ),
    # ── Programação ──
    "github": SiteInfo(
        nome="github",
        url="https://github.com",
        sinonimos=["github", "git hub"],
        categoria="programacao",
    ),
    "gitlab": SiteInfo(
        nome="gitlab",
        url="https://gitlab.com",
        sinonimos=["gitlab", "git lab"],
        categoria="programacao",
    ),
    "bitbucket": SiteInfo(
        nome="bitbucket",
        url="https://bitbucket.org",
        sinonimos=["bitbucket", "bit bucket"],
        categoria="programacao",
    ),
    "stackoverflow": SiteInfo(
        nome="stackoverflow",
        url="https://stackoverflow.com",
        sinonimos=["stackoverflow", "stack overflow", "so"],
        categoria="programacao",
    ),
    "python": SiteInfo(
        nome="python",
        url="https://www.python.org",
        sinonimos=["python", "python org"],
        categoria="programacao",
    ),
    "pypi": SiteInfo(
        nome="pypi",
        url="https://pypi.org",
        sinonimos=["pypi", "pip"],
        categoria="programacao",
    ),
    "dockerhub": SiteInfo(
        nome="dockerhub",
        url="https://hub.docker.com",
        sinonimos=["dockerhub", "docker hub", "docker"],
        categoria="programacao",
    ),
    "npm": SiteInfo(
        nome="npm",
        url="https://www.npmjs.com",
        sinonimos=["npm", "npmjs"],
        categoria="programacao",
    ),
    "vscodemarketplace": SiteInfo(
        nome="vscodemarketplace",
        url="https://marketplace.visualstudio.com",
        sinonimos=["vscode marketplace", "visual studio marketplace", "extensions vscode"],
        categoria="programacao",
    ),
    "jetbrains": SiteInfo(
        nome="jetbrains",
        url="https://www.jetbrains.com",
        sinonimos=["jetbrains", "jet brains", "intellij"],
        categoria="programacao",
    ),
    # ── Google ──
    "gmail": SiteInfo(
        nome="gmail",
        url="https://mail.google.com",
        sinonimos=["gmail", "google mail", "email google", "correio google"],
        categoria="google",
    ),
    "googledrive": SiteInfo(
        nome="googledrive",
        url="https://drive.google.com",
        sinonimos=["google drive", "drive google", "google drive"],
        categoria="google",
    ),
    "googledocs": SiteInfo(
        nome="googledocs",
        url="https://docs.google.com",
        sinonimos=["google docs", "docs google", "documentos google"],
        categoria="google",
    ),
    "googlesheets": SiteInfo(
        nome="googlesheets",
        url="https://sheets.google.com",
        sinonimos=["google sheets", "sheets google", "planilhas google"],
        categoria="google",
    ),
    "googleslides": SiteInfo(
        nome="googleslides",
        url="https://slides.google.com",
        sinonimos=["google slides", "slides google", "apresentacoes google"],
        categoria="google",
    ),
    "googleforms": SiteInfo(
        nome="googleforms",
        url="https://forms.google.com",
        sinonimos=["google forms", "forms google", "formularios google"],
        categoria="google",
    ),
    "googlemeet": SiteInfo(
        nome="googlemeet",
        url="https://meet.google.com",
        sinonimos=["google meet", "meet google", "google meetings"],
        categoria="google",
    ),
    "googleagenda": SiteInfo(
        nome="googleagenda",
        url="https://calendar.google.com",
        sinonimos=["google agenda", "google calendar", "calendar google", "agenda google"],
        categoria="google",
    ),
    "googlemaps": SiteInfo(
        nome="googlemaps",
        url="https://maps.google.com",
        sinonimos=["google maps", "maps google", "mapas google"],
        categoria="google",
    ),
    "googletradutor": SiteInfo(
        nome="googletradutor",
        url="https://translate.google.com",
        sinonimos=["google tradutor", "translate google", "google translate", "tradutor google"],
        categoria="google",
    ),
    "googlefotos": SiteInfo(
        nome="googlefotos",
        url="https://photos.google.com",
        sinonimos=["google fotos", "photos google", "google photos", "fotos google"],
        categoria="google",
    ),
    "googlekeep": SiteInfo(
        nome="googlekeep",
        url="https://keep.google.com",
        sinonimos=["google keep", "keep google", "google notas"],
        categoria="google",
    ),
    # ── Microsoft ──
    "outlook": SiteInfo(
        nome="outlook",
        url="https://outlook.live.com",
        sinonimos=["outlook", "outlook live", "hotmail", "email microsoft"],
        categoria="microsoft",
    ),
    "onedrive": SiteInfo(
        nome="onedrive",
        url="https://onedrive.live.com",
        sinonimos=["onedrive", "one drive", "microsoft onedrive"],
        categoria="microsoft",
    ),
    "teams": SiteInfo(
        nome="teams",
        url="https://teams.microsoft.com",
        sinonimos=["teams", "microsoft teams", "teams microsoft"],
        categoria="microsoft",
    ),
    "microsoft365": SiteInfo(
        nome="microsoft365",
        url="https://www.office.com",
        sinonimos=["microsoft 365", "office 365", "office", "microsoft office"],
        categoria="microsoft",
    ),
    "azure": SiteInfo(
        nome="azure",
        url="https://portal.azure.com",
        sinonimos=["azure", "microsoft azure", "azure portal"],
        categoria="microsoft",
    ),
    "powerbi": SiteInfo(
        nome="powerbi",
        url="https://app.powerbi.com",
        sinonimos=["power bi", "powerbi", "microsoft power bi"],
        categoria="microsoft",
    ),
    # ── Trabalho ──
    "notion": SiteInfo(
        nome="notion",
        url="https://www.notion.so",
        sinonimos=["notion"],
        categoria="trabalho",
    ),
    "trello": SiteInfo(
        nome="trello",
        url="https://trello.com",
        sinonimos=["trello"],
        categoria="trabalho",
    ),
    "jira": SiteInfo(
        nome="jira",
        url="https://www.atlassian.com/software/jira",
        sinonimos=["jira", "jira software"],
        categoria="trabalho",
    ),
    "confluence": SiteInfo(
        nome="confluence",
        url="https://www.atlassian.com/software/confluence",
        sinonimos=["confluence"],
        categoria="trabalho",
    ),
    "slack": SiteInfo(
        nome="slack",
        url="https://slack.com",
        sinonimos=["slack"],
        categoria="trabalho",
    ),
    "zoom": SiteInfo(
        nome="zoom",
        url="https://zoom.us",
        sinonimos=["zoom"],
        categoria="trabalho",
    ),
    "canva": SiteInfo(
        nome="canva",
        url="https://www.canva.com",
        sinonimos=["canva"],
        categoria="trabalho",
    ),
    "figma": SiteInfo(
        nome="figma",
        url="https://www.figma.com",
        sinonimos=["figma"],
        categoria="trabalho",
    ),
    "miro": SiteInfo(
        nome="miro",
        url="https://miro.com",
        sinonimos=["miro", "miro board", "realtime board"],
        categoria="trabalho",
    ),
    "clickup": SiteInfo(
        nome="clickup",
        url="https://clickup.com",
        sinonimos=["clickup", "click up"],
        categoria="trabalho",
    ),
    "monday": SiteInfo(
        nome="monday",
        url="https://monday.com",
        sinonimos=["monday", "monday.com", "monday dot com"],
        categoria="trabalho",
    ),
    "asana": SiteInfo(
        nome="asana",
        url="https://asana.com",
        sinonimos=["asana"],
        categoria="trabalho",
    ),
    # ── Redes Sociais ──
    "youtube": SiteInfo(
        nome="youtube",
        url="https://www.youtube.com",
        sinonimos=["youtube", "you tube", "yt"],
        categoria="redes_sociais",
    ),
    "facebook": SiteInfo(
        nome="facebook",
        url="https://www.facebook.com",
        sinonimos=["facebook", "face", "fb", "face book"],
        categoria="redes_sociais",
    ),
    "instagram": SiteInfo(
        nome="instagram",
        url="https://www.instagram.com",
        sinonimos=["instagram", "insta", "ig"],
        categoria="redes_sociais",
    ),
    "threads": SiteInfo(
        nome="threads",
        url="https://www.threads.net",
        sinonimos=["threads", "threads net"],
        categoria="redes_sociais",
    ),
    "x": SiteInfo(
        nome="x",
        url="https://x.com",
        sinonimos=["x", "twitter"],
        categoria="redes_sociais",
    ),
    "tiktok": SiteInfo(
        nome="tiktok",
        url="https://www.tiktok.com",
        sinonimos=["tiktok", "tik tok", "tt"],
        categoria="redes_sociais",
    ),
    "linkedin": SiteInfo(
        nome="linkedin",
        url="https://www.linkedin.com",
        sinonimos=["linkedin", "linked in", "in"],
        categoria="redes_sociais",
    ),
    "reddit": SiteInfo(
        nome="reddit",
        url="https://www.reddit.com",
        sinonimos=["reddit", "redd"],
        categoria="redes_sociais",
    ),
    "discord": SiteInfo(
        nome="discord",
        url="https://discord.com",
        sinonimos=["discord"],
        categoria="redes_sociais",
    ),
    "pinterest": SiteInfo(
        nome="pinterest",
        url="https://www.pinterest.com",
        sinonimos=["pinterest", "pins"],
        categoria="redes_sociais",
    ),
    # ── Streaming ──
    "netflix": SiteInfo(
        nome="netflix",
        url="https://www.netflix.com",
        sinonimos=["netflix", "net flex", "netflix.com"],
        categoria="streaming",
    ),
    "primevideo": SiteInfo(
        nome="primevideo",
        url="https://www.primevideo.com",
        sinonimos=["prime video", "primevideo", "amazon prime video", "amazon prime"],
        categoria="streaming",
    ),
    "disneyplus": SiteInfo(
        nome="disneyplus",
        url="https://www.disneyplus.com",
        sinonimos=["disney plus", "disneyplus", "disney+"],
        categoria="streaming",
    ),
    "max": SiteInfo(
        nome="max",
        url="https://www.max.com",
        sinonimos=["max", "hbo max", "hbomax"],
        categoria="streaming",
    ),
    "crunchyroll": SiteInfo(
        nome="crunchyroll",
        url="https://www.crunchyroll.com",
        sinonimos=["crunchyroll", "crunchy roll"],
        categoria="streaming",
    ),
    "spotify": SiteInfo(
        nome="spotify",
        url="https://open.spotify.com",
        sinonimos=["spotify", "spotify web", "spotify player"],
        categoria="streaming",
    ),
    "deezer": SiteInfo(
        nome="deezer",
        url="https://www.deezer.com",
        sinonimos=["deezer"],
        categoria="streaming",
    ),
    "twitch": SiteInfo(
        nome="twitch",
        url="https://www.twitch.tv",
        sinonimos=["twitch", "twitch tv", "twitch.tv"],
        categoria="streaming",
    ),
    # ── Compras ──
    "amazon": SiteInfo(
        nome="amazon",
        url="https://www.amazon.com.br",
        sinonimos=["amazon", "amazon brasil"],
        categoria="compras",
    ),
    "mercadolivre": SiteInfo(
        nome="mercadolivre",
        url="https://www.mercadolivre.com.br",
        sinonimos=["mercado livre", "mercadolivre", "ml"],
        categoria="compras",
    ),
    "shopee": SiteInfo(
        nome="shopee",
        url="https://shopee.com.br",
        sinonimos=["shopee", "shoppe"],
        categoria="compras",
    ),
    "aliexpress": SiteInfo(
        nome="aliexpress",
        url="https://www.aliexpress.com",
        sinonimos=["aliexpress", "ali express", "aliex"],
        categoria="compras",
    ),
    "magazineluiza": SiteInfo(
        nome="magazineluiza",
        url="https://www.magazineluiza.com.br",
        sinonimos=["magazine luiza", "magazineluiza", "magalu"],
        categoria="compras",
    ),
    "kabum": SiteInfo(
        nome="kabum",
        url="https://www.kabum.com.br",
        sinonimos=["kabum", "ka bumm", "ka bu m"],
        categoria="compras",
    ),
    "casasbahia": SiteInfo(
        nome="casasbahia",
        url="https://www.casasbahia.com.br",
        sinonimos=["casas bahia", "casasbahia"],
        categoria="compras",
    ),
    # ── Bancos ──
    "nubank": SiteInfo(
        nome="nubank",
        url="https://nubank.com.br",
        sinonimos=["nubank", "nu bank", "nu"],
        categoria="bancos",
    ),
    "bancodobrasil": SiteInfo(
        nome="bancodobrasil",
        url="https://www.bb.com.br",
        sinonimos=["banco do brasil", "bancodobrasil", "bb", "banco brasil"],
        categoria="bancos",
    ),
    "caixa": SiteInfo(
        nome="caixa",
        url="https://www.caixa.gov.br",
        sinonimos=["caixa", "caixa economica", "cef"],
        categoria="bancos",
    ),
    "itau": SiteInfo(
        nome="itau",
        url="https://www.itau.com.br",
        sinonimos=["itau", "itau", "banco itau"],
        categoria="bancos",
    ),
    "bradesco": SiteInfo(
        nome="bradesco",
        url="https://www.bradesco.com.br",
        sinonimos=["bradesco", "banco bradesco"],
        categoria="bancos",
    ),
    "santander": SiteInfo(
        nome="santander",
        url="https://www.santander.com.br",
        sinonimos=["santander", "banco santander"],
        categoria="bancos",
    ),
    "inter": SiteInfo(
        nome="inter",
        url="https://www.bancointer.com.br",
        sinonimos=["inter", "banco inter", "bancointer"],
        categoria="bancos",
    ),
    "c6bank": SiteInfo(
        nome="c6bank",
        url="https://www.c6bank.com.br",
        sinonimos=["c6 bank", "c6bank", "c6"],
        categoria="bancos",
    ),
    "picpay": SiteInfo(
        nome="picpay",
        url="https://picpay.com.br",
        sinonimos=["picpay", "pic pay"],
        categoria="bancos",
    ),
    # ── Educação ──
    "coursera": SiteInfo(
        nome="coursera",
        url="https://www.coursera.org",
        sinonimos=["coursera"],
        categoria="educacao",
    ),
    "udemy": SiteInfo(
        nome="udemy",
        url="https://www.udemy.com",
        sinonimos=["udemy"],
        categoria="educacao",
    ),
    "alura": SiteInfo(
        nome="alura",
        url="https://www.alura.com.br",
        sinonimos=["alura", "alura cursos", "alura online"],
        categoria="educacao",
    ),
    "khanacademy": SiteInfo(
        nome="khanacademy",
        url="https://www.khanacademy.org",
        sinonimos=["khan academy", "khanacademy"],
        categoria="educacao",
    ),
    "edx": SiteInfo(
        nome="edx",
        url="https://www.edx.org",
        sinonimos=["edx", "edx org"],
        categoria="educacao",
    ),
    "duolingo": SiteInfo(
        nome="duolingo",
        url="https://www.duolingo.com",
        sinonimos=["duolingo", "duo lingo"],
        categoria="educacao",
    ),
    "w3schools": SiteInfo(
        nome="w3schools",
        url="https://www.w3schools.com",
        sinonimos=["w3schools", "w3 schools", "w3"],
        categoria="educacao",
    ),
    "mdnwebdocs": SiteInfo(
        nome="mdnwebdocs",
        url="https://developer.mozilla.org",
        sinonimos=["mdn", "mdn web docs", "mozilla developer", "developer mozilla"],
        categoria="educacao",
    ),
    # ── Notícias ──
    "g1": SiteInfo(
        nome="g1",
        url="https://g1.globo.com",
        sinonimos=["g1", "globo g1", "g1 globo"],
        categoria="noticias",
    ),
    "uol": SiteInfo(
        nome="uol",
        url="https://www.uol.com.br",
        sinonimos=["uol", "universo online"],
        categoria="noticias",
    ),
    "cnnbrasil": SiteInfo(
        nome="cnnbrasil",
        url="https://www.cnnbrasil.com.br",
        sinonimos=["cnn brasil", "cnnbrasil", "cnn"],
        categoria="noticias",
    ),
    "bbc": SiteInfo(
        nome="bbc",
        url="https://www.bbc.com",
        sinonimos=["bbc", "bbc news", "bbc news brasil"],
        categoria="noticias",
    ),
    "reuters": SiteInfo(
        nome="reuters",
        url="https://www.reuters.com",
        sinonimos=["reuters", "reuters news"],
        categoria="noticias",
    ),
    "folhadespaulo": SiteInfo(
        nome="folhadespaulo",
        url="https://www.folha.uol.com.br",
        sinonimos=["folha de sao paulo", "folha", "folhadespaulo", "folha de s.paulo"],
        categoria="noticias",
    ),
    "estadao": SiteInfo(
        nome="estadao",
        url="https://www.estadao.com.br",
        sinonimos=["estadao", "estadão", "o estado de sao paulo"],
        categoria="noticias",
    ),
}
