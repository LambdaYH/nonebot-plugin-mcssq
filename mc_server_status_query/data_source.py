from pathlib import Path
from typing import Optional

from mcstatus import BedrockServer, JavaServer
from nonebot.log import logger
from nonebot.adapters.onebot.v11 import MessageSegment

from .model import ServerDB
from .draw import draw_bedrock, draw_java, draw_error, draw_list

data_path = Path() / "data" / "mcserver"
db_file = data_path / "mcserver.db"

data_path.mkdir(exist_ok=True, parents=True)

mcserverdb = ServerDB(db_file)


def add_server(group_id: int, user_id: int, name: str, host: str, sv_type: str):
    if mcserverdb.get_server(group_id=group_id, user_id=user_id, name=name):
        return False
    host_port = host.split(":")
    port = None
    if len(host_port) == 2:
        host = host_port[0]
        port = int(host_port[1])
    mcserverdb.add_server(
        group_id=group_id,
        user_id=user_id,
        name=name,
        host=host,
        port=port,
        sv_type=sv_type,
    )
    return True


def del_server(group_id: int, user_id: int, name: str):
    if not mcserverdb.get_server(group_id=group_id, user_id=user_id, name=name):
        return False
    mcserverdb.del_server(group_id=group_id, user_id=user_id, name=name)
    return True


def get_server_info(group_id: int, user_id: int, name: str):
    if detail := mcserverdb.get_server(group_id=group_id, user_id=user_id, name=name):
        return (
            detail[0],
            detail[1],
            detail[2],
        )
    return None


async def server_status(host: str, port: Optional[int], sv_type: str):
    try:
        if sv_type == "je":
            status = await JavaServer(host=host, port=port).async_status()
            return MessageSegment.image(draw_java(status))
        else:
            status = await BedrockServer(host=host, port=port).async_status()
            return MessageSegment.image(draw_bedrock(status))
    except Exception as e:
        logger.warning(f"MC服务器查询失败：\nhost：{host}\nport：{port}\n类型：{sv_type}")
        return MessageSegment.image(draw_error(e=e, sv_type=sv_type))


def get_mc_list(group_id: int, user_id: int):
    servers = mcserverdb.get_server_list(group_id=group_id, user_id=user_id)
    if not servers:
        return MessageSegment.image(draw_list("空"))
    server_text_list = []
    for server in servers:
        server_text_list.append(
            f"§b{server[0]}§7 "
            + ("Java版" if server[3] == "je" else "基岩版")
            + f"\n§f{server[1]}"
            + (f":{server[2]}" if server[2] else "")
        )
    return MessageSegment.image(draw_list("\n".join(server_text_list)))
