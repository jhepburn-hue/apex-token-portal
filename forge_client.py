import os
import requests
from pathlib import Path

FORGE_BASE_URL = "https://forge.wavelynxdev.com"

ACTIVE_IAP_COOKIE = "AVF5qOE9oVvH5GwK1o3K5uPUzS_F6dCiGOrZ6gpCBQg7u6S6gZZEWZzuVV2SeTkNCTmfAkTHMRwkpTJxQ8s8AJxGNQ7i3IwkRAgXzWK0V4dR8d3PAzN8I3pLrdrJySyjtgnVMegmEVbQa73lUXZyuUnVyKMXnXYsYl5nKvtIg_Z2Q89YRmonj6C3QRp62QOYCvOntI8w5cvqHMsf2shAafkHqdzXNnUalF1Gwchj1IktlLZpBEX8iFi7oJPRQUVZ2ZbM2pOkWMxc8BeIP_ECky8UuA3L35-tPmrnpuTse1M79BsYSlzZ7xpua3t3XyfIQ48xEn7xLVW4zPe_OpVg6zdCa2rWCJN4nX1gYI9HsTTpZ9J8eIXiln9STe3s7JXoUe3nB5GYjaN25sNDzcy--L6HCFhaIRKHL0uWNmoLb8dhmxYIM_CALWKr024nxAfjejcUW7CBBgO-PFubI1uGGzIGAmKLXm7wP6nLhgbEmsK42JIDDgh06qVi9l4-LhUN0sgpiFrBtpeJsSQOGdDxXRWwIXlGR4EkffDiAMqssN7P98_0aeISCQhBIbMBzY9hoIQ18U2QJJsSjXH6J-oi5FyBdTDAx4kRYSHs5hFWpEyF6sS_dMM-bfYo-K0TvpNW-gHcAK93Ys3lPrXDSocnqBcUabldLwHYBXKGO811BTPAzCIApjjAtdzCMlzMCKnrOzaLgm3W0jhKQ5JoGWS7cBnisQQTTp_RhoHV4K8Tk17nvItCY8dwfsQSoQB2QMJLqh6x-I-Evcr1VThd9SMC7YGfKDzZfJqcW2BvWZ4s3SQzHO68UeosspfmoLtLa43b3GISbvpJ_SKkSF4rI8EAjs7tc_X7bZgwp8PxBWXtRcXDOtuwXwRgEisX_V3yexJFmhHQBAmrUA24lW1zhyQs12xB6TNqx1UwwCvjxVa8utVEBra7Z-n1P9505hEbRuE8K2JQbXK4VPXfP0Dyw0LT_Z1nCq_ObnLCNmQb9Rl02UTdP8b2O3U5H3EiZSpkBjwVwprpWHgpcv06nK0i4scFBBAov_vcoYPx3ykL3ry5BUIt03ue4T2OzCVbrVmIzQhuG02Ldh3_yi5lW_AKDuG8-kcGtqTRsEHZTeGG2syodcILPKFSA2i76fBUBcWrNlNVOZTaykCxxBAQstDmBpfgEbiBP8c6ssw5Xqfy14Z5ci1SNmDhRtvCtw7Fkl3iYuHsKOrJkTutumwnrNrjxcCc2JK3ruAGvH1Z6HxwnnYkVLMvOCMKSm17-DbWxb8Y_fs85mIV3ZijsmJcGIUp0absul7DN82ZwzGphK0y0qn72M0bAY4APZFGZ1QuZZFzU9C90kvAe1Wsj8ueUthU-BEQlSkqiGbNtz5RxLIQTD8ZPcoYlQe9N_KrK-Tn10q_HSo1s5TPcrPqDgOEUFvye97QT9wdj31_xLUTmijIMTwwxdGwB4H2kxYt4UMMgDaH4dVKAuW7ZULwaHifJ99R_QAs9gBMxaaD2izCBtqjVgDyUYY-1WlJs738LxMvIh7ky2upPfgc9U967RIzfRMZPb6-cdBL36H7mWIwnYvlvNM7awovdNcpzsEJfw1b6RT1IAq8ojsuq-j8JjeTxjDlbEyCBZUOo-WJ6SirtRcbatKquSQ5uDkFOAnbvogdAaWC99MItyxZy_nNlhe4ATc_H9eUo2QtMAD2BiozY_4IybUWP8g"
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