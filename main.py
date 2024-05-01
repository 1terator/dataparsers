import asyncio
import re
import uuid
from typing import Any, Tuple

from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter
from openpyxl.workbook import Workbook

from cantonfair.service import CantonfairParseService
from eccmid.service import EccmidParseService
from firabarcelona.service import FiraBarcelonaParseService
from ifema.service import IFemaParseService
from mwcbarcelona.service import MVCBarcelonaParseService
from publicalt.service import PublicaltParseService
from services import WhatsappService
from ticketsnebext.service import TicketsNebextParseService
from tools import validate_phone_number, recreate_phone_number


def generate_excel_filename(filename: str) -> str:
    return filename + f"_{str(uuid.uuid4())[:6]}.xlsx"


def is_href(text: str) -> bool:
    return True if re.fullmatch(r"(?P<url>https?://[^\s]+)", text) else False


def to_excel(parsed_data_names: Tuple, parsed_data: Any, sheet_name: str) -> Workbook:
    print(parsed_data)
    workbook = Workbook()
    workbook_sheet = workbook.active
    workbook_sheet.title = sheet_name

    for i in range(len(parsed_data_names)):
        workbook_sheet.cell(row=1, column=i + 1).value = str(parsed_data_names[i])
        workbook_sheet.cell(row=1, column=i + 1).font = Font(bold=True)
        workbook_sheet.column_dimensions[get_column_letter(i+1)].width = 50

    global_step = 1
    for i in range(len(parsed_data)):
        local_step = 0
        for j in range(len(parsed_data[i])):
            if not isinstance(parsed_data[i][j], list):
                if not parsed_data[i][j]:
                    continue
                data = ILLEGAL_CHARACTERS_RE.sub(r'', str(parsed_data[i][j]))
                workbook_sheet.cell(row=i + 1 + global_step, column=j + 1).value = data
                if is_href(text=str(parsed_data[i][j])):
                    workbook_sheet.cell(row=i + 1 + global_step, column=j + 1).style = "Hyperlink"
                    workbook_sheet.cell(row=i + 1 + global_step, column=j + 1).hyperlink = data
                continue
            for k in range(len(parsed_data[i][j])):
                if not parsed_data[i][j][k]:
                    continue
                data = ILLEGAL_CHARACTERS_RE.sub(r'', str(parsed_data[i][j][k]))
                workbook_sheet.cell(row=i + k + 1 + global_step, column=j + 1).value = data
                if is_href(text=str(parsed_data[i][j][k])):
                    workbook_sheet.cell(row=i + k + 1 + global_step, column=j + 1).style = "Hyperlink"
                    workbook_sheet.cell(row=i + k + 1 + global_step, column=j + 1).hyperlink = data
            local_step = max(local_step, len(parsed_data[i][j]) - 1)
        global_step += local_step

    return workbook


async def main():
    filename: str = "Eccmid2024"

    whatsapp = WhatsappService(7103909222, "0b7c68fbd0284e098b454ef95d925bf43c48b75d0cc14415a7")
    # publicalt = PublicaltParseService("ExpoBeautyBarcelona2024", whatsapp)
    # ticketsnebext = TicketsNebextParseService("advanced_factories_2024", whatsapp)
    # mwcbarcelona = MVCBarcelonaParseService("00422c3d9f3484bccfae011262fcf49a", "8VVB6VR33K", whatsapp)
    # ifema = IFemaParseService("3a88c5e5-a6e1-4898-b72b-103e4eed1731", "1a015dd8-4c05-4192-2715-08db8781d84f", whatsapp)
    # hispack = FiraBarcelonaParseService("J011024", 136, "hispack2024", whatsapp)
    # bridal = FiraBarcelonaParseService("J113024", 137, whatsapp)
    # iotswc24 = FiraBarcelonaParseService("J025024", 138, "construmat2024", whatsapp)
    eccmid = EccmidParseService(whatsapp)
    excel = to_excel(
        parsed_data_names=eccmid.get_parsed_data_names(),
        parsed_data=await eccmid.parse(),
        sheet_name=filename
    )
    await asyncio.to_thread(excel.save, filename=generate_excel_filename(filename))


def format_phone_number(phone_number: str) -> str:
    if not phone_number:
        return phone_number
    phone_number: str = str(int("".join(ch for ch in phone_number if ch.isdigit())))
    return "34" + phone_number if not 11 <= len(phone_number) else phone_number


async def phones(filename: str):
    whatsapp = WhatsappService(7103909222, "0b7c68fbd0284e098b454ef95d925bf43c48b75d0cc14415a7")
    phones_list = []

    with open(filename) as my_file:
        for line in my_file:
            whatsapp_link: str = await whatsapp.format_to_whatsapp_link(
                format_phone_number(recreate_phone_number(line))
            )
            phones_list.append(whatsapp_link if whatsapp_link else "")

    with open("results.txt", "w") as my_file:
        my_file.writelines([phone + "\n" for phone in phones_list])


async def test(filename: str):
    whatsapp = WhatsappService(7103909222, "0b7c68fbd0284e098b454ef95d925bf43c48b75d0cc14415a7")
    canton = CantonfairParseService("FL_wcLIqs9juTaaPEzSHnofohz5QBpfqevRnSj4wFkfjlSt_31IWIjSw-iQRwgb41mVMoawNE3axd660K7wWXqLeYuRAl06-Aj5Pnt1cKK7W3GvPL9QVTtz0hmrvcnvOM11Bj_dJyN8HNQDURXB6bx-EeGzj7JWmIwQaUUG34nMMqd6uGuuZSq6ue1yf0kRtuTLfVZAdPIhi4z_lUvOobvhnWUqFQvv1sNd6DbKQepVqxslkTvRDjA36AB294qeDWZjRsmKrTg1wL_lQej3nv8321tzaL1pQwtrExabDbve8D3LkfVrkXqU1dutE5Apjaj4nOib8TjA8xF5HBZ4xLobyz5f2xlld7a_8RJRLeQ3HDWyguRcCpdWBxxSe1CCdagKw_dxwEmDflosgNJLE3X9v6_Z6tUXjNX7x1enbmmFxLO38xWf1QQTxZK7PaCxFgpLvScK8Asu3qazDqx6mMKiPvviy4KwiKz-vsUQzSr84Dj27-aHcK--6nXgj0OJNYUDNCl25NUS2QtNjfry4c8ktpA_5PFbt2AYdDi4J5WYvvtlIMYO5hfBGSt11Fm8H-z4vdUpWbfYauedFR-fMALXtDZp2wi3RS0RmPxeg6O6WLVUm-N-Aoi1B2l_NutJGlqKfADRaInxifbb-l9CxvfDcU1Y3lSYNGYomMDwS5W29IOpFCGSkpoYfbNkiKveShujdJxkoWY_7m1IyUSSY6XpOoar8EdO9tuknvzkhhrZAwMcslFVZYvM_rAVTL6Hlt3dXPjPBPQmaUre9ttENaKpMZE5N6r9f4v7WAFPZpjWYZgU0L-97PJJJI9MdJ14In6NJ_mGc2kYGiQIZlzYoEXn3st_nlrZvgDBIXsqWU0C_Y2YCqeA5UMsLG06JQTwsZQ3EvWpT9TJJKasu848g8aUa3Ma4G7eNibKa-88qNgRKctRTIZjiyYpmjyvyjEGesaS8D-_zPLIPeW3b_Ke23NKGp6q1JDLMlu_ORfIfA50ipvgIHbaHKkG-85xW48sl30UxKIylU6mAPjf2xLNARQosCFKm_UDgfria2IVCqM7j087R0a4CkW-Dd3h7nejE2LVdgHi5JYGytNI0Ka7xlJz7FViHHksNiP2YQe4hdbiUaZc0xJct5w7Xj-nXNYeO-ZgKCI83a4e3ekAsWViheBJtjBF3fNHCP0fDFPiXjGYVmT72e53TH4OxVEGRLJ0Ygs05GHDx8IFqNvwa3My6v-74_euj29SdWNRhF__Lkw4evTvDyeqOLFUoPI4Cjqe88rEduYeu617Q2fESjQw4l0yQNkfVvSzjiDK1UUZI-CUxnxps1LJaGjRboxiU77pyM2ZoEhJ5xwTt0__WNr9KKdFEWrmohNBIdVd3Kp_QarG_guIyWZv-_B1vOkfCk5zr0Dpl0HsFczJYLNRCfftx0JLzw==", whatsapp)

    excel = to_excel(
        parsed_data_names=canton.get_parsed_data_names(),
        parsed_data=await canton.parse(),
        sheet_name=filename
    )
    await asyncio.to_thread(excel.save, filename=generate_excel_filename(filename))


# asyncio.run(main())
# asyncio.run(phones("phones.txt"))
asyncio.run(test("Cantonfair2024"))
