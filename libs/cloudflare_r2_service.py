import os
from dotenv import load_dotenv
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

# 加载 .env 文件中的环境变量
load_dotenv()

# 从环境变量获取 R2 配置
R2_ENDPOINT_URL = os.getenv("CLOUDFLARE_R2_ENDPOINT")
R2_ACCESS_KEY_ID = os.getenv("CLOUDFLARE_R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("CLOUDFLARE_R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.getenv("CLOUDFLARE_R2_BUCKET_NAME")
R2_PUBLIC_ACCESS_DOMAIN = os.getenv("CLOUDFLARE_R2_PUBLIC_ACCESS_DOMAIN")

# 确保所有必要的配置都已加载
if not all(
    [
        R2_ENDPOINT_URL,
        R2_ACCESS_KEY_ID,
        R2_SECRET_ACCESS_KEY,
        R2_BUCKET_NAME,
        R2_PUBLIC_ACCESS_DOMAIN,
    ]
):
    raise ValueError(
        "错误：请在 .env 文件中配置所有必要的 Cloudflare R2 凭据和存储桶名称/公共访问域名。"
    )

# 创建 S3 客户端
s3_client = boto3.client(
    service_name="s3",
    endpoint_url=R2_ENDPOINT_URL,
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    region_name="auto",  # R2 通常使用 'auto' 区域
)


def upload_file_to_r2(file_path: str, path_prefix: str = "") -> str | None:
    """
    将文件上传到 Cloudflare R2 存储桶。

    Args:
        file_path: 要上传的本地文件路径。
        path_prefix: 在 R2 存储桶中的路径前缀（例如，"images/"）。

    Returns:
        上传文件的公共 URL，如果上传失败则返回 None。
    """
    if not os.path.exists(file_path):
        print(f"错误：文件不存在 - {file_path}")
        return None

    # 构建 R2 中的对象键
    file_name = os.path.basename(file_path)
    object_key = os.path.join(path_prefix, file_name).replace(
        "\\", "/"
    )  # 确保使用正斜杠

    try:
        # 上传文件
        s3_client.upload_file(file_path, R2_BUCKET_NAME, object_key)

        # 构建公共 URL
        # 使用公共访问域名和对象键
        public_url = f"https://{R2_PUBLIC_ACCESS_DOMAIN}/{object_key}"

        # print(f"文件 {file_name} 已成功上传到 R2，对象键为 {object_key}")
        return public_url

    except FileNotFoundError:
        print(f"错误：文件未找到 - {file_path}")
        return None
    except NoCredentialsError:
        print("错误：未找到 AWS 凭据。请检查你的环境变量或配置文件。")
        return None
    except PartialCredentialsError:
        print("错误：凭据不完整。请检查你的 AWS 凭据配置。")
        return None
    except Exception as e:
        print(f"上传文件到 R2 时发生错误：{e}")
        return None
