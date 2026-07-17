import os
import requests
from pathlib import Path

FORGE_BASE_URL = "https://forge.wavelynxdev.com"

ACTIVE_IAP_COOKIE = "AVF5qOHevIzxsvS-V4kgaoUt0nXY3HwbwIGBEbS4qbNQXk0Q_MUDjrIqbBZqz9fdVzK8EvRT3JGcshJPBn5HiJuWV7IzvD-Vbk0Ux0BDHDF90ZtFLg30rX0CX9LIYhEomPre7zU96coNBXtpDNjN3yY_WEUlpU7_TUo0D2pX8ytMMInRsd79NzZx9dhPHFKr0ZcYScGY3jGsnsEAfGlHPwNFNdVS7F82KCh7N7woB2YPeUiC98xAhoXFoz6YPF3YgWYspMTLWHZBaliUC_4bw-zvNt25YigdNs3YUeaNNKIKIuoDuA9GtqFiF_zYWvmH2wrLL9JDnicRglB8NkBZluYdhgH4tv5bd-AOy11KhFn41iZBufZXeb5wtld7zlxtw7UNaUjl6Qbtm8p0THX9BmT3SekLXy6JQEoc2ALS0ClLspEsrvtDwy41Xeg85LzghQEI3T5eFqTZH8sy3lkA2v4ucxVR2kkfYais5PlbkF8gJoQQspYdtRzcAskEwUBRXM-yITVcz-4Swhfa2jcTIFLIrtBLDxVPGaQkmXgwQ4x94Pi4tbkEtGbsNJHa8qD8CqKIDFPznmQTl1x76cgTFm0_9Abl5UlKiaN4NHnLW-BwMW8E79nFsAneZY4JFeuDYLqvvJGY3rVTbFmoXqoaC_e0RhTOTJuoGf2i2IuDsxeHKmlS2OisV8M8YTCF3GAjmGTILjMv2OeGzDCwbZHzMglTGjip6saB7L8RM3MyDix1Tbg-C-WIZs1AtZkttbUPM52j68XWZb5d1GfydimVWAx-_bamd8CsqzyAUrNqblD9JKf4Pbl-zDRDDfy1nv30gt8F9evkdLlSwfC2UPTIfdsx4mSbzW962GLMwJr_G3rDXfBdllOW0sY02FjOP520RbBFmoJvhoCsoX_dzwCtT5ThDS7icr7rK5LWNfhXY8tqqZi7YmCclkPGPNfA2qx9Yl0zz_g_sm7OsJ2HvoNZ3drLOQcFSCtLDhG8QsdHNr-l3myFNEesjnMMCIOtOBf2kih2M84wdnPnxSdNYTb604e3oKG1yalXkQqGd1QQNiQpxfLY9U4KdSC83o_s-RarKZvuXc9vqkfyUqnAzT7orAUFjYD-2X7ykETiRuog9q-knOtsv8rBhX-mJOEFlLPEeF3VAuYktgDEG_nR6jN2qBQ-_lq4G5AFkv3vKCuoUrLLzRm9WhKZrcQTWCUf2J1OpTBfGkTBU8hMw1QqTF-xe-sEqRbvuGAKXJVP_fZ3NzSmICnMHF9DI7WLqW4_t7e7aY66aRjHsTBVwi36rkDHnKn0csgBPeO2AR0y5EefuewtWgg1DPXjSRbtmAYkibYzpnMHq1SJ7WhvR4j768ZOvH2D9FKCRKXV7Svg3pBXMifp86jETXjXmAGNf1yVTuUNXi2AZxbtp2pg-eCBQQjJhvvKeWt72HMQN3E_t1me5HaOjYK73zdbTD2wyZO3ckPAWnk_Fh2M9TGXe7PJI6lZyLloOYcQauPUH-nB1-vCYNhP2zVAzoKkbGGUtJVXqLm9AcuRt1xB4kAnoX0ChuGrNRqixfk2B1RGk2iGDEj_GmL0IOYFl8bVp2RTZ6zMI3O4E7yyx28uLqLlnEJCIW-t_CwtfgoPzxppjJ1ZitqbviJy1jFYbMhXlwEqVFlrnFgLLdpVPUEgCDg3tWnF_SA02KNqC3Eq7CY_qylTZIPo0zm-VdU-9Vir"
ACTIVE_IAP_UID = "112564004525954034965"


class ForgeClient:
    def __init__(self, base_url: str = FORGE_BASE_URL):
        self.base_url = base_url.rstrip("/")

    def _get_auth_headers(self) -> dict:
        return {
            "Cookie": f"__Host-GCP_IAP_AUTH_TOKEN_A82A7FE83D3A1171={ACTIVE_IAP_COOKIE}; GCP_IAP_UID={ACTIVE_IAP_UID}",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        }

    def import_csv_config(
        self, csv_file_path: Path, target_version: str
    ) -> requests.Response:
        url = f"{self.base_url}/configs/import"
        headers = self._get_auth_headers()

        with open(csv_file_path, "rb") as f:
            files = {"upload": (csv_file_path.name, f, "text/csv")}
            data = {"target_version": target_version}

            response = requests.post(
                url,
                files=files,
                data=data,
                headers=headers,
                allow_redirects=False,
                timeout=30,
            )

        return response

    def trigger_config_build(
        self,
        config_name: str,
        version: str,
        firmware_build_id: str,
        source: str = "user",
        firmware_source: str = "Release",
        include_partials: str = "0",
        gitlab_ref: str = "master",
    ) -> requests.Response:
        url = f"{self.base_url}/configs/build"
        headers = self._get_auth_headers()

        payload = {
            "version": version,
            "source": source,
            "firmware_source": firmware_source,
            "firmware_build_id": firmware_build_id,
            "gitlab_ref": gitlab_ref,
            "include_partials": include_partials,
        }

        if include_partials == "1":
            payload["partial_config_name"] = config_name
        else:
            payload["config_name"] = config_name

        response = requests.post(
            url, data=payload, headers=headers, allow_redirects=False, timeout=30
        )

        return response