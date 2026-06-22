import { useCallback, useEffect, useRef, useState } from 'react'

/** 画布节点模型选择：与 config 同步，且避免 undefined 覆盖用户已选值 */
export function useCanvasModelCode(
  configModelCode: string | undefined,
  nodeId: string,
  configRevision?: string,
) {
  const [modelCode, setModelCodeState] = useState(configModelCode || '')
  const modelCodeRef = useRef(modelCode)
  modelCodeRef.current = modelCode

  useEffect(() => {
    if (configModelCode) {
      setModelCodeState(configModelCode)
      modelCodeRef.current = configModelCode
    }
  }, [nodeId, configRevision, configModelCode])

  const setModelCode = useCallback((code: string) => {
    modelCodeRef.current = code
    setModelCodeState(code)
  }, [])

  return { modelCode, setModelCode, modelCodeRef }
}
