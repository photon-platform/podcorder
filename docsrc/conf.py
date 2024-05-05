#  from ablog.conf import *
from photon_platform.sphinxilator.global_conf import *
import photon_platform.podcorder as module

version = module.__version__

org = "photon-platform"
org_name = "photon-platform"

repo = "podcorder"
repo_name = "podcorder"

setup_globals(org, org_name, repo, repo_name)
