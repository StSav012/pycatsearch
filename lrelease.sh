L_RELEASE="../qt-linguist/lrelease.py"
if [[ -e ${L_RELEASE} ]]; then L_RELEASE="python ${L_RELEASE}"; else L_RELEASE="pyside6-lrelease"; fi
echo using "${L_RELEASE}"
find src/pycatsearch/gui/i18n -maxdepth 1 -iname "*.ts" -type f \
  -exec sh -c "L_RELEASE=\"${L_RELEASE}\""' ${L_RELEASE} ${0} -qm ${0%.*}.qm ${@:1}' {} "$@" \;
