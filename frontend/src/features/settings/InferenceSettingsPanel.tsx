import { useEffect, useState, type FormEvent } from 'react';
import { Cpu } from 'lucide-react';
import { requestJson } from '../../shared/api/httpClient';
import { Button, Surface } from '../../shared/ui';

type ModelSettings = Record<string, string | number>;
const ROLES = [
  { key: 'llm', label: '답변 생성·질문 분해' },
  { key: 'vlm', label: 'VLM 이미지·표 구조 분석' },
  { key: 'embedding', label: '검색 임베딩' },
] as const;

export function InferenceSettingsPanel() {
  const [settings, setSettings] = useState<ModelSettings | null>(null);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [saving, setSaving] = useState(false);
  const [probing, setProbing] = useState(false);
  const [statuses, setStatuses] = useState<Record<string, { detail: string }>>({});

  useEffect(() => {
    const controller = new AbortController();
    requestJson<ModelSettings>('/api/settings/inference', { signal: controller.signal })
      .then(setSettings)
      .catch((reason: unknown) => {
        if (!controller.signal.aborted) setError(reason instanceof Error ? reason.message : '모델 설정을 읽지 못했습니다.');
      });
    return () => controller.abort();
  }, []);

  function change(key: string, value: string | number) {
    setSettings((previous) => previous ? { ...previous, [key]: value } : previous);
    setMessage('');
  }

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError('');
    try {
      await requestJson('/api/settings/inference', { method: 'PUT', json: settings });
      setMessage('저장했습니다. 실행 중인 FastAPI를 종료한 뒤 다시 실행하면 적용됩니다. 임베딩 모델을 바꾸면 파일을 새로 적재하세요.');
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : '설정을 저장하지 못했습니다.');
    } finally {
      setSaving(false);
    }
  }

  async function probe() {
    setProbing(true);
    setError('');
    try {
      setStatuses(await requestJson('/api/settings/inference/status'));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : '모델 서버 상태를 읽지 못했습니다.');
    } finally {
      setProbing(false);
    }
  }

  return (
    <Surface className="settings-section">
      <div className="settings-section__header">
        <div className="settings-section__title">
          <Cpu size={19} />
          <div><h2>모델 실행 방식</h2><p>OpenAI API 또는 GPU의 llama.cpp 서버를 선택합니다.</p></div>
        </div>
        <Button type="button" busy={probing} disabled={probing} onClick={probe}>서버 연결 확인</Button>
      </div>
      {error ? <p role="alert" className="text-rose-700">{error}</p> : null}
      {!settings && !error ? <p role="status">모델 설정을 읽는 중입니다.</p> : null}
      {settings ? (
        <form onSubmit={save} className="space-y-5">
          {ROLES.map(({ key, label }) => {
            const provider = String(settings[`${key}_provider`]);
            const modelKey = provider === 'llamacpp' ? `llama_cpp_${key}_model` : `openai_${key}_model`;
            return (
              <fieldset key={key} className="space-y-2 rounded border border-slate-200 p-3">
                <legend className="px-1 font-semibold">{label}</legend>
                {statuses[key] ? <p className="text-sm text-slate-600">현재 적용 설정: {statuses[key].detail}</p> : null}
                <label className="block text-sm">
                  제공자
                  <select className="ml-2 rounded border p-1" value={provider} onChange={(event) => change(`${key}_provider`, event.target.value)}>
                    <option value="openai">OpenAI API</option><option value="llamacpp">로컬 llama.cpp</option>
                  </select>
                </label>
                <label className="block text-sm">
                  모델 ID
                  <input className="ml-2 w-64 rounded border p-1" required value={String(settings[modelKey])} onChange={(event) => change(modelKey, event.target.value)} />
                </label>
                {provider === 'llamacpp' ? (
                  <label className="block text-sm">
                    llama.cpp API 주소
                    <input type="url" className="ml-2 w-80 rounded border p-1" required value={String(settings[`llama_cpp_${key}_url`])} onChange={(event) => change(`llama_cpp_${key}_url`, event.target.value)} />
                  </label>
                ) : <p className="text-xs text-slate-600">API 키는 .env의 OPENAI_API_KEY를 사용합니다.</p>}
                {key === 'embedding' && provider === 'llamacpp' ? (
                  <label className="block text-sm">
                    벡터 차원 (BGE-M3: 1024)
                    <input type="number" min={1} max={16000} className="ml-2 w-24 rounded border p-1" required value={settings.llama_cpp_embedding_dimension} onChange={(event) => change('llama_cpp_embedding_dimension', Number(event.target.value))} />
                  </label>
                ) : null}
              </fieldset>
            );
          })}
          <p className="text-sm text-slate-600">로컬 VLM에는 이미지 지원 GGUF와 mmproj가 필요합니다. 모델 ID는 서버 실행 시 지정한 별칭과 일치해야 합니다.</p>
          <Button type="submit" busy={saving} disabled={saving}>모델 설정 저장</Button>
          {message ? <p role="status" className="text-emerald-800">{message}</p> : null}
        </form>
      ) : null}
    </Surface>
  );
}
