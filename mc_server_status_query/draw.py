import base64
import socket
import random
from io import BytesIO
from pathlib import Path
from asyncio.exceptions import TimeoutError
from typing import Literal, Optional, Union, List
from string import ascii_letters, digits, punctuation
from PIL.Image import Resampling

from mcstatus.bedrock_status import BedrockStatusResponse
from mcstatus.pinger import PingResponse
from nonebot_plugin_imageutils import BuildImage, Text2Image
from nonebot_plugin_imageutils.fonts import add_font

CODE_COLOR = {
    "0": "#000000",
    "1": "#0000AA",
    "2": "#00AA00",
    "3": "#00AAAA",
    "4": "#AA0000",
    "5": "#AA00AA",
    "6": "#FFAA00",
    "7": "#AAAAAA",
    "8": "#555555",
    "9": "#5555FF",
    "a": "#55FF55",
    "b": "#55FFFF",
    "c": "#FF5555",
    "d": "#FF55FF",
    "e": "#FFFF55",
    "f": "#FFFFFF",
    "g": "#DDD605",
}

STROKE_COLOR = {
    "0": "#000000",
    "1": "#00002A",
    "2": "#002A00",
    "3": "#002A2A",
    "4": "#2A0000",
    "5": "#2A002A",
    "6": "#2A2A00",
    "7": "#2A2A2A",
    "8": "#151515",
    "9": "#15153F",
    "a": "#153F15",
    "b": "#153F3F",
    "c": "#3F1515",
    "d": "#3F153F",
    "e": "#3F3F15",
    "f": "#3F3F3F",
    "g": "#373501",
}

STRING_COLOR = {
    "black": "0",
    "dark_blue": "1",
    "dark_green": "2",
    "dark_aqua": "3",
    "dark_red": "4",
    "dark_purple": "5",
    "gold": "6",
    "gray": "7",
    "dark_gray": "8",
    "blue": "9",
    "green": "a",
    "aqua": "b",
    "red": "c",
    "light_purple": "d",
    "yellow": "e",
    "white": "f",
}

STYLE_BBCODE = {
    "l": ["[b]", "[/b]"],
    "m": ["", ""],  # 不支持
    "n": ["", ""],  # 不支持
    "o": ["", ""],  # 不支持
}

GAME_MODE_MAP = {"Survival": "生存", "Creative": "创造", "Adventure": "冒险"}

RANDOM_CHAR_TEMPLATE = ascii_letters + digits + punctuation

ServerType = Literal["je", "be"]

MARGIN = 32
MIN_WIDTH = 512
FONT_NAME = "unifont"
TITLE_FONT_SIZE = 8 * 5
EXTRA_FONT_SIZE = 8 * 4
EXTRA_STROKE_WIDTH = 2
STROKE_RATIO = 0.0625
EXTRA_SPACING = 12

JE_HEADER = "[MCJE服务器信息]"
BE_HEADER = "[MCBE服务器信息]"
SUCCESS_TITLE = "请求成功"

MODULE_DIR = Path(__file__).parent
RES_DIR = MODULE_DIR / "res"

GRASS_RES_PATH = RES_DIR / "grass_side_carried.png"
DIRT_RES_PATH = RES_DIR / "dirt.png"
DEFAULT_ICON_PATH = RES_DIR / "default.png"

GRASS_RES = BuildImage.open(GRASS_RES_PATH)
DIRT_RES = BuildImage.open(DIRT_RES_PATH)
DEFAULT_ICON_RES = BuildImage.open(DEFAULT_ICON_PATH)

from nonebot import get_driver

driver = get_driver()


@driver.on_startup
async def _():
    await add_font("unifont.ttf", RES_DIR / "unifont.ttf")


def get_latency_color(delay: Union[int, float]) -> str:
    if delay <= 50:
        return "a"
    if delay <= 100:
        return "e"
    if delay <= 200:
        return "6"
    return "c"


def random_char(length: int) -> str:
    return "".join(random.choices(RANDOM_CHAR_TEMPLATE, k=length))


def format_code_to_bbcode(text: str) -> str:
    if not text:
        return text

    parts = text.split("§")
    parsed: List[str] = [parts[0]]
    color_tails: List[str] = []
    format_tails: List[str] = []

    for p in parts[1:]:
        char = p[0]
        txt = p[1:]

        if char in CODE_COLOR:
            parsed.extend(color_tails)
            color_tails.clear()
            parsed.append(f"[stroke={STROKE_COLOR[char]}][color={CODE_COLOR[char]}]")
            color_tails.append("[/color][/stroke]")

        elif char in STYLE_BBCODE:
            head, tail = STYLE_BBCODE[char]
            format_tails.append(tail)
            parsed.append(head)

        elif char == "r":  # reset
            parsed.extend(color_tails)
            parsed.extend(format_tails)

        elif char == "k":  # random
            txt = random_char(len(txt))

        else:
            txt = f"§{char}{txt}"

        parsed.append(txt)

    parsed.extend(color_tails)
    parsed.extend(format_tails)
    return "\n".join([x.strip() for x in "".join(parsed).splitlines()])


def format_list(sample: List[str], items_per_line=2, line_start_spaces=10, list_gap=2):
    if not sample:
        return ""

    max_width = max([len(x) for x in sample]) + list_gap

    line_added = 0
    tmp = []
    for name in sample:
        if line_added < items_per_line:
            name = name.ljust(max_width)

        tmp.append(name)
        line_added += 1

        if line_added >= items_per_line:
            tmp.append("\n")
            tmp.append(" " * line_start_spaces)
            line_added = 0

    return "".join(tmp)


def get_header_by_sv_type(sv_type: ServerType) -> str:
    return JE_HEADER if sv_type == "je" else BE_HEADER


def draw_bg(width: int, height: int) -> BuildImage:
    size = DIRT_RES.width
    bg = BuildImage.new("RGBA", (width, height))

    for hi in range(0, height, size):
        for wi in range(0, width, size):
            bg.paste(DIRT_RES if hi else GRASS_RES, (wi, hi))

    return bg


def build_img(
    header1: str,
    header2: str,
    extra: Optional[Text2Image] = None,
    icon: Optional[BuildImage] = None,
) -> BytesIO:
    if not icon:
        icon = DEFAULT_ICON_RES

    HEADER_TEXT_COLOR = CODE_COLOR["f"]
    HEADER_STROKE_COLOR = STROKE_COLOR["f"]

    HEADER_HEIGHT = 128
    HALF_HEADER_HEIGHT = int(HEADER_HEIGHT / 2)

    BG_WIDTH = extra.width + MARGIN * 2 if extra else MIN_WIDTH
    BG_HEIGHT = HEADER_HEIGHT + MARGIN * 2
    if BG_WIDTH < MIN_WIDTH:
        BG_WIDTH = MIN_WIDTH
    if extra:
        BG_HEIGHT += extra.height + int(MARGIN / 2)
    bg = draw_bg(BG_WIDTH, BG_HEIGHT)

    if icon.size != (HEADER_HEIGHT, HEADER_HEIGHT):
        icon = icon.resize_height(
            HEADER_HEIGHT, inside=False, resample=Resampling.NEAREST
        )
    bg.paste(icon, (MARGIN, MARGIN), alpha=True)

    bg.draw_text(
        (
            HEADER_HEIGHT + MARGIN + MARGIN / 2,
            MARGIN - 4,
            BG_WIDTH - MARGIN,
            HALF_HEADER_HEIGHT + MARGIN + 4,
        ),
        header1,
        halign="left",
        fill=HEADER_TEXT_COLOR,
        max_fontsize=TITLE_FONT_SIZE,
        fontname=FONT_NAME,
        stroke_ratio=STROKE_RATIO,
        stroke_fill=HEADER_STROKE_COLOR,
    )
    bg.draw_text(
        (
            HEADER_HEIGHT + MARGIN + MARGIN / 2,
            HALF_HEADER_HEIGHT + MARGIN - 4,
            BG_WIDTH - MARGIN,
            HEADER_HEIGHT + MARGIN + 4,
        ),
        header2,
        halign="left",
        fill=HEADER_TEXT_COLOR,
        max_fontsize=TITLE_FONT_SIZE,
        fontname=FONT_NAME,
        stroke_ratio=STROKE_RATIO,
        stroke_fill=HEADER_STROKE_COLOR,
    )

    if extra:
        extra.draw_on_image(
            bg.image,
            (MARGIN, int(HEADER_HEIGHT + MARGIN + MARGIN / 2)),
        )

    return bg.convert("RGB").save("PNG")


def format_extra(extra: str) -> Text2Image:
    return Text2Image.from_bbcode_text(
        format_code_to_bbcode(extra),
        EXTRA_FONT_SIZE,
        fill=CODE_COLOR["f"],
        fontname=FONT_NAME,
        stroke_ratio=STROKE_RATIO,
        stroke_fill=STROKE_COLOR["f"],
        spacing=EXTRA_SPACING,
    )


def draw_java(res: PingResponse) -> BytesIO:
    icon = None
    if res.favicon:
        icon = BuildImage.open(BytesIO(base64.b64decode(res.favicon.split(",")[-1])))

    players_online = res.players.online
    players_max = res.players.max
    online_percent = round(players_online / players_max * 100, 2)

    player_li = ""
    if res.players.sample:
        sample = [x.name for x in res.players.sample]
        player_li = f"\n§7玩家列表: §f{format_list(sample)}"

    mod_client = ""
    mod_total = ""
    mod_list = ""
    if mod_info := res.raw.get("modinfo"):
        if tmp := mod_info.get("type"):
            mod_client = f"§7Mod端类型: §f{tmp}\n"

        if tmp := mod_info.get("modList"):
            mod_total = f"§7Mod总数: §f{len(tmp)}\n"
            mod_list = f"§7Mod列表: §f{format_list(tmp)}\n"  # type: ignore

    extra_txt = (
        f"{res.description}§r\n"
        f"§7服务端名: §f{res.version.name}\n"
        f"{mod_client}"
        f"§7协议版本: §f{res.version.protocol}\n"
        f"§7当前人数: §f{players_online}/{players_max} ({online_percent}%)\n"
        f"{mod_total}"
        f"§7测试延迟: §{get_latency_color(res.latency)}{res.latency:.2f}ms"
        f"{player_li}"
        f"{mod_list}"
    )
    return build_img(JE_HEADER, SUCCESS_TITLE, format_extra(extra_txt), icon)


def draw_bedrock(res: BedrockStatusResponse) -> BytesIO:
    map_name = f"§7存档名称: §f{res.map}§r\n" if res.map else ""
    game_mode = (
        f"§7游戏模式: §f{GAME_MODE_MAP.get(res.gamemode, res.gamemode)}\n"
        if res.gamemode
        else ""
    )
    online_percent = round(int(res.players_online) / int(res.players_max) * 100, 2)

    extra_txt = (
        f"{res.motd}§r\n"
        f"§7协议版本: §f{res.version.protocol}\n"
        f"§7游戏版本: §f{res.version.version}\n"
        f"§7在线人数: §f{res.players_online}/{res.players_max} ({online_percent}%)\n"
        f"{map_name}"
        f"{game_mode}"
        f"§7测试延迟: §{get_latency_color(res.latency)}{res.latency:.2f}ms"
    )
    return build_img(BE_HEADER, SUCCESS_TITLE, format_extra(extra_txt))


def draw_error(e: Exception, sv_type: ServerType) -> BytesIO:
    extra = ""
    if isinstance(e, TimeoutError):
        reason = "请求超时"
    elif isinstance(e, socket.gaierror):
        reason = "域名解析失败"
        extra = str(e)
    else:
        reason = "出错了！"
        extra = repr(e)

    if extra:
        extra = format_extra(extra).wrap(MIN_WIDTH - MARGIN * 2)

    return build_img(get_header_by_sv_type(sv_type), reason, extra)


def draw_list(list_text: str) -> BytesIO:
    list_text = format_extra(list_text)
    BG_WIDTH = list_text.width + MARGIN * 2 if list_text else MIN_WIDTH
    BG_HEIGHT = MARGIN * 2 + list_text.height
    if BG_WIDTH < MIN_WIDTH:
        BG_WIDTH = MIN_WIDTH
    bg = draw_bg(BG_WIDTH, BG_HEIGHT)
    list_text.draw_on_image(
        bg.image,
        (MARGIN, MARGIN),
    )

    return bg.convert("RGB").save("PNG")
