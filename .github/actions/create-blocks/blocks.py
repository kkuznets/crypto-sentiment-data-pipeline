"""
python blocks.py -b $GITHUB_REF_NAME -r "$GITHUB_SERVER_URL/$GITHUB_REPOSITORY" \
-n ${{ inputs.gh_block_name }} -i ${{ inputs.image_uri }} --crj ${{ inputs.crj_block_name }} --region ${{ inputs.region }}
"""
import argparse
from prefect.filesystems import GitHub
from prefect_gcp.cloud_run import CloudRunJob
from prefect_gcp.credentials import GcpCredentials

REPO = "https://github.com/anna-geller/prefect-cloud-gcp"
parser = argparse.ArgumentParser()
parser.add_argument("-b", "--branch", default="main")
parser.add_argument("-r", "--repo", default=REPO)

parser.add_argument("-n", "--gh-block-name", default="default-gh")
parser.add_argument("-i", "--image")
parser.add_argument("--crj", "--crj-block-name", default="default-crj")
parser.add_argument("--region", default="us-central1")

args = parser.parse_args()

gh = GitHub(repository=args.repo, reference=args.branch)
gh.save(args.gh_block_name, overwrite=True)

block = CloudRunJob(
    image=args.image,
    region=args.region,
    credentials=GcpCredentials.load(args.crj_block_name),
    cpu=1,
    timeout=3600,
)
block.save(args.crj_block_name, overwrite=True)
