"""
python blocks.py -b $GITHUB_REF_NAME -r "$GITHUB_SERVER_URL/$GITHUB_REPOSITORY" \
-n ${{ inputs.storage_block }} -i ${{ inputs.image_uri }} --gcp ${{ inputs.gcp_creds_block }} --crj ${{ inputs.infrastructure_block }} --region ${{ inputs.region }}
"""
import argparse
from prefect.filesystems import GitHub
from prefect_gcp.cloud_run import CloudRunJob
from prefect_gcp.credentials import GcpCredentials

REPO = "https://github.com/anna-geller/prefect-cloud-gcp"
parser = argparse.ArgumentParser()
parser.add_argument("-b", "--branch", default="main")
parser.add_argument("-r", "--repo", default=REPO)

parser.add_argument("-n", "--storage-block", default="default-gh")
parser.add_argument("-i", "--image")
parser.add_argument("--gcp", "--gcp-creds-block", default="default-gcp")
parser.add_argument("--crj", "--infrastructure-block", default="default-crj")
parser.add_argument("--region", default="us-central1")

args = parser.parse_args()

gh = GitHub(repository=args.repo, reference=args.branch)
gh.save(args.storage_block, overwrite=True)

block = CloudRunJob(
    image=args.image,
    region=args.region,
    credentials=GcpCredentials.load(args.gcp_creds_block),
    cpu=1,
    timeout=3600,
)
block.save(args.infrastructure_block, overwrite=True)
