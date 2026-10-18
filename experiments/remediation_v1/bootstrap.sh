#!/usr/bin/env bash
set -euo pipefail
ROOT="$(pwd)"
mkdir -p build/remediation_v1
# Official repositories, exact retained commits; patch only this isolated clone.
git clone --filter=blob:none https://github.com/contiki-ng/contiki-ng.git build/remediation_v1/contiki
git -C build/remediation_v1/contiki checkout 4ccd1a3b9e767f168d12ec3df187fe6b7dc736b5
git clone --filter=blob:none https://github.com/contiki-ng/cooja.git build/remediation_v1/cooja
git -C build/remediation_v1/cooja checkout fabff3ee41eeeb6f3de7bd11f7c9cdf0a7d7dfc4
git -C build/remediation_v1/contiki apply "$ROOT/hardware/cooja_feedback/cooja-radio-observer.patch"
cd build/remediation_v1/cooja
./gradlew jar
