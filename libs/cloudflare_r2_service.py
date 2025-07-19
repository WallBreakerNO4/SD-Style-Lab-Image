import os
import asyncio
from dotenv import load_dotenv
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from tqdm import tqdm

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


def upload_file_to_r2(
    file_path: str, path_prefix: str = "", cache_control: str | None = None
) -> str | None:
    """
    将文件上传到 Cloudflare R2 存储桶。

    Args:
        file_path: 要上传的本地文件路径。
        path_prefix: 在 R2 存储桶中的路径前缀（例如，"images/"）。
        cache_control: 设置 Cache-Control 标头（例如，"public, max-age=3600"）。

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
        # 构建 ExtraArgs
        extra_args = {}
        if cache_control:
            extra_args["CacheControl"] = cache_control

        # 上传文件
        s3_client.upload_file(
            file_path, R2_BUCKET_NAME, object_key, ExtraArgs=extra_args
        )

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


def remove_dir_in_r2(path_prefix: str) -> None:
    """
    删除 R2 存储桶中的指定路径前缀。

    Args:
        path_prefix: 要删除的路径前缀（例如，"images/"）。
    """
    try:
        # 使用分页器列出所有匹配前缀的对象
        paginator = s3_client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=R2_BUCKET_NAME, Prefix=path_prefix)

        objects_to_delete = []
        total_objects = 0

        for page in pages:
            if "Contents" in page:
                objects_to_delete.extend(
                    [{"Key": obj["Key"]} for obj in page["Contents"]]
                )
                total_objects += len(page["Contents"])

        if not objects_to_delete:
            print(f"没有找到匹配的对象：{path_prefix}")
            return

        print(f"找到 {total_objects} 个对象需要删除，路径前缀：{path_prefix}")

        # 批量删除对象，每次最多 1000 个
        chunk_size = 1000
        for i in tqdm(range(0, len(objects_to_delete), chunk_size), desc="删除对象"):
            chunk = objects_to_delete[i : i + chunk_size]
            s3_client.delete_objects(
                Bucket=R2_BUCKET_NAME,
                Delete={
                    "Objects": chunk,
                    "Quiet": True,
                },  # Quiet=True 避免返回成功删除的对象列表
            )

        print(f"已删除 R2 中的路径前缀：{path_prefix}")

    except Exception as e:
        print(f"删除 R2 中的路径前缀时发生错误：{e}")


async def aio_upload_file_to_r2(
    semaphore: asyncio.Semaphore,
    file_path: str,
    index: int,
    path_prefix: str = "",
    cache_control: str | None = None,
) -> tuple[str | None, int]:
    """
    使用线程池将文件异步上传到 Cloudflare R2 存储桶，并受并发限制。

    Args:
        semaphore: 用于控制并发的 asyncio.Semaphore 对象。
        file_path: 要上传的本地文件路径。
        path_prefix: 在 R2 存储桶中的路径前缀（例如，"images/"）。
        cache_control: 设置 Cache-Control 标头。

    Returns:
        上传文件的公共 URL，如果上传失败则返回 None。
    """
    async with semaphore:
        # 在一个单独的线程中运行同步的 upload_file_to_r2 函数
        # 使用 asyncio.to_thread (Python 3.9+)
        public_url = await asyncio.to_thread(
            upload_file_to_r2, file_path, path_prefix, cache_control
        )

    return public_url, index


def change_cache_control_dir_in_r2(path_prefix: str, cache_control: str) -> None:
    """
    批量更改 R2 存储桶中指定路径前缀下所有文件的 Cache-Control 属性。

    Args:
        path_prefix: 要更改的路径前缀（例如，"images/"）。
        cache_control: 新的 Cache-Control 值（例如，"public, max-age=31536000"）。
    """
    try:
        # 使用分页器列出所有匹配前缀的对象
        paginator = s3_client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=R2_BUCKET_NAME, Prefix=path_prefix)

        objects_to_update = []
        for page in pages:
            if "Contents" in page:
                objects_to_update.extend(page["Contents"])

        if not objects_to_update:
            print(f"没有找到匹配的对象：{path_prefix}")
            return

        print(
            f"找到 {len(objects_to_update)} 个对象需要更新 Cache-Control，路径前缀：{path_prefix}"
        )

        # 遍历并更新每个对象的 Cache-Control
        for obj in tqdm(objects_to_update, desc="更新 Cache-Control"):
            object_key = obj["Key"]
            copy_source = {"Bucket": R2_BUCKET_NAME, "Key": object_key}

            # 获取对象的现有元数据，只替换 Cache-Control
            # 注意：R2 可能不支持直接获取所有元数据，因此我们只专注于更新 Cache-Control
            s3_client.copy_object(
                Bucket=R2_BUCKET_NAME,
                CopySource=copy_source,
                Key=object_key,
                MetadataDirective="REPLACE",
                CacheControl=cache_control,
            )

        print(f"已成功更新路径前缀 {path_prefix} 的 Cache-Control 为 '{cache_control}'")

    except Exception as e:
        print(f"更新 R2 中路径前缀的 Cache-Control 时发生错误：{e}")


async def aio_change_cache_control_dir_in_r2(
    semaphore: asyncio.Semaphore, path_prefix: str, cache_control: str
) -> None:
    """
    使用线程池异步批量更改 R2 存储桶中指定路径前缀下所有文件的 Cache-Control 属性。

    Args:
        semaphore: 用于控制并发的 asyncio.Semaphore 对象。
        path_prefix: 要更改的路径前缀（例如，"images/"）。
        cache_control: 新的 Cache-Control 值（例如，"public, max-age=31536000"）。
    """
    async with semaphore:
        await asyncio.to_thread(
            change_cache_control_dir_in_r2, path_prefix, cache_control
        )
