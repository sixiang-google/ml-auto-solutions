# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A DAG to run MaxText inference benchmarks with nightly version."""

import datetime
from airflow import models
from airflow.models.baseoperator import chain
from dags import composer_env, test_owner
from dags.vm_resource import TpuVersion, Zone, Project, V5_NETWORKS, V5E_SUBNETWORKS, V5P_SUBNETWORKS, RuntimeVersion
from dags.inference.configs import maxtext_inference_gce_config
from dags.multipod.configs.common import SetupMode, Platform


# Run once a day at 4 am UTC (8 pm PST)
SCHEDULED_TIME = "0 4 * * *" if composer_env.is_prod_env() else None


with models.DAG(
    dag_id="maxtext_inference",
    schedule=SCHEDULED_TIME,
    tags=["inference_team", "maxtext", "nightly", "benchmark"],
    start_date=datetime.datetime(2024, 1, 19),
    catchup=False,
) as dag:
  test_name_prefix = "maxtext-inference"
  test_models = {
      "llama2-7b": {
          "sleep_time": 120,
          "tpu_version_cores": [(TpuVersion.V5E, 8), (TpuVersion.V5P, 8)],
          "checkpoint": "gs://inference-benchmarks/models/llama2-7b/2024-04-25-14-01/param-only-decode-ckpt-maxtext/checkpoints/0/items",
          "model_mode": "base",
          "maxtext_logs": "gs://inference-benchmarks/models/llama2-7b/2024-04-25-14-01/",
          "scan_layers": "false",
          "dataset": "openorca",
          "weight_dtype": "bfloat16",
          "tokenizer": "tokenizer.llama2",
          "per_device_batch_sizes": [1, 2, 4, 8, 11, 12],
          # (ici_fsdp_parallelism, ici_autoregressive_parallelism, ici_tensor_parallelism)
          "ici_parallelisms": [(1, -1, 1), (1, 1, -1)],
          "request_rate": 5,
          "num_prompts": 1000,
          "max_prefill_predict_length": 1024,
          "max_target_length": 2048,
          "max_output_length": 1024,
      },
      "llama2-13b": {
          "sleep_time": 120,
          "tpu_version_cores": [(TpuVersion.V5E, 8), (TpuVersion.V5P, 8)],
          "checkpoint": "gs://inference-benchmarks/models/llama2-13b/2024-04-25-14-01/param-only-decode-ckpt-maxtext/checkpoints/0/items",
          "model_mode": "base",
          "maxtext_logs": "gs://inference-benchmarks/models/llama2-13b/2024-04-25-14-01/",
          "scan_layers": "false",
          "dataset": "openorca",
          "weight_dtype": "bfloat16",
          "tokenizer": "tokenizer.llama2",
          "per_device_batch_sizes": [1, 2, 4, 5, 6],
          # (ici_fsdp_parallelism, ici_autoregressive_parallelism, ici_tensor_parallelism)
          "ici_parallelisms": [(1, -1, 1), (1, 1, -1)],
          "request_rate": 5,
          "num_prompts": 1000,
          "max_prefill_predict_length": 1024,
          "max_target_length": 2048,
          "max_output_length": 1024,
      },
      "llama2-70b": {
          "sleep_time": 240,
          "tpu_version_cores": [(TpuVersion.V5P, 8)],
          "per_device_batch_sizes": [12, 16, 20, 24],
          "checkpoint": "gs://inference-benchmarks/models/llama2-70b-chat/2024-05-08-23-16/param-only-decode-ckpt-maxtext/checkpoints/0/items",
          "model_mode": "chat",
          "maxtext_logs": "gs://inference-benchmarks/models/llama2-70b-chat/2024-05-08-23-16/",
          "scan_layers": "false",
          "dataset": "openorca",
          "weight_dtype": "bfloat16",
          "tokenizer": "tokenizer.llama2",
          # (ici_fsdp_parallelism, ici_autoregressive_parallelism, ici_tensor_parallelism)
          "ici_parallelisms": [(1, -1, 1), (1, 1, -1)],
          "request_rate": 5,
          "num_prompts": 1000,
          "max_prefill_predict_length": 1024,
          "max_target_length": 2048,
          "max_output_length": 1024,
      },
      "gemma-7b": {
          "sleep_time": 120,
          "tpu_version_cores": [(TpuVersion.V5E, 8), (TpuVersion.V5P, 8)],
          "checkpoint": "gs://inference-benchmarks/models/gemma-7b/2024-04-25-14-01/param-only-decode-ckpt-maxtext/checkpoints/0/items",
          "model_mode": "base",
          "maxtext_logs": "gs://inference-benchmarks/models/gemma-7b/2024-04-25-14-01/",
          "scan_layers": "false",
          "dataset": "openorca",
          "weight_dtype": "bfloat16",
          "tokenizer": "tokenizer.gemma",
          "per_device_batch_sizes": [1, 2, 4, 8, 11, 12],
          # (ici_fsdp_parallelism, ici_autoregressive_parallelism, ici_tensor_parallelism)
          "ici_parallelisms": [(1, -1, 1), (1, 1, -1)],
          "request_rate": 5,
          "num_prompts": 1000,
          "max_prefill_predict_length": 1024,
          "max_target_length": 2048,
          "max_output_length": 1024,
      },
      "mixtral-8x7b": {
          "sleep_time": 240,
          # Unquantized checkpoint only loads on v5p
          "tpu_version_cores": [(TpuVersion.V5P, 8)],
          "per_device_batch_sizes": [80, 128],
          # checkpoint created using these instructions - go/mixtral-inference-testing
          "checkpoint": "gs://vipannalla_mixtral_ckpt/moe_matmul/moe_matmul_06_15_24/checkpoints/0/items/",
          "model_mode": "instruct",
          "maxtext_logs": "gs://inference-benchmarks/models/mixtral-8x7b-instruct/2024-06-18/",
          "scan_layers": "false",
          "dataset": "openorca",
          "weight_dtype": "bfloat16",
          "tokenizer": "gs://maxtext-external/mixtral-8x7B-v0.1-Instruct/tokenizer.mistral",
          # (ici_fsdp_parallelism, ici_autoregressive_parallelism, ici_tensor_parallelism)
          "ici_parallelisms": [(1, -1, 1), (1, 1, -1)],
          "request_rate": 5,
          "num_prompts": 1000,
          "max_prefill_predict_length": 2048,
          "max_target_length": 3072,
          "max_output_length": 1024,
          # Only used for MoE models
          "moe_matmul": "true",
      },
  }

  for model, sweep_model_configs in test_models.items():
    # tasks_per_model = []
    for per_device_batch_size in sweep_model_configs["per_device_batch_sizes"]:
      for ici_parallelism in sweep_model_configs["ici_parallelisms"]:
        for tpu_version, tpu_cores in sweep_model_configs["tpu_version_cores"]:
          # Set per_device_batch_size to a single value, not a list
          model_configs = {}
          model_configs["model_name"] = model
          model_configs["model_mode"] = sweep_model_configs["model_mode"]
          model_configs["sleep_time"] = sweep_model_configs["sleep_time"]
          model_configs["checkpoint"] = sweep_model_configs["checkpoint"]
          model_configs["maxtext_logs"] = sweep_model_configs["maxtext_logs"]
          model_configs["scan_layers"] = sweep_model_configs["scan_layers"]
          model_configs["dataset"] = sweep_model_configs["dataset"]
          model_configs["weight_dtype"] = sweep_model_configs["weight_dtype"]
          model_configs["tokenizer"] = sweep_model_configs["tokenizer"]
          model_configs["per_device_batch_size"] = per_device_batch_size
          ici_fsdp = ici_parallelism[0]
          ici_ar = ici_parallelism[1]
          ici_tensor = ici_parallelism[2]
          model_configs["ici_fsdp_parallelism"] = ici_fsdp
          model_configs["ici_autoregressive_parallelism"] = ici_ar
          model_configs["ici_tensor_parallelism"] = ici_tensor
          model_configs["request_rate"] = sweep_model_configs["request_rate"]
          model_configs["num_prompts"] = sweep_model_configs["num_prompts"]
          model_configs["max_target_length"] = sweep_model_configs[
              "max_target_length"
          ]
          model_configs["max_prefill_predict_length"] = sweep_model_configs[
              "max_prefill_predict_length"
          ]
          model_configs["max_output_length"] = sweep_model_configs[
              "max_output_length"
          ]
          model_configs["moe_matmul"] = sweep_model_configs.get(
              "moe_matmul", "false"
          )
          if tpu_version == TpuVersion.V5E:
            # v5e benchmarks
            project_name = Project.TPU_PROD_ENV_AUTOMATED.value
            zone = Zone.US_EAST1_C.value
            network = V5_NETWORKS
            subnetwork = V5E_SUBNETWORKS
            runtime_version = RuntimeVersion.V2_ALPHA_TPUV5_LITE.value
          elif tpu_version == TpuVersion.V5P:
            zone = Zone.US_EAST5_A.value
            runtime_version = RuntimeVersion.V2_ALPHA_TPUV5.value
            project_name = Project.TPU_PROD_ENV_AUTOMATED.value
            network = V5_NETWORKS
            subnetwork = V5P_SUBNETWORKS

          maxtext_stable_1slice = maxtext_inference_gce_config.get_maxtext_inference_nightly_config(
              tpu_version=tpu_version,
              tpu_cores=tpu_cores,
              tpu_zone=zone,
              runtime_version=runtime_version,
              project_name=project_name,
              time_out_in_min=60,
              is_tpu_reserved=True,
              test_name=f"{test_name_prefix}-stable-{model}-per_device_batch_size-{per_device_batch_size}-ici-fsdp{ici_fsdp}-ar{ici_ar}-tensor{ici_tensor}",
              test_mode=SetupMode.STABLE,
              network=network,
              subnetwork=subnetwork,
              model_configs=model_configs,
          )
          maxtext_nightly_1slice = maxtext_inference_gce_config.get_maxtext_inference_nightly_config(
              tpu_version=tpu_version,
              tpu_cores=tpu_cores,
              tpu_zone=zone,
              runtime_version=runtime_version,
              project_name=project_name,
              time_out_in_min=60,
              is_tpu_reserved=True,
              test_name=f"{test_name_prefix}-nightly-{model}-per_device_batch_size-{per_device_batch_size}-ici-fsdp{ici_fsdp}-ar{ici_ar}-tensor{ici_tensor}",
              test_mode=SetupMode.NIGHTLY,
              network=network,
              subnetwork=subnetwork,
              model_configs=model_configs,
          )
          maxtext_stable_1slice >> maxtext_nightly_1slice
