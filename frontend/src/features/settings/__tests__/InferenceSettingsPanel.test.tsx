import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { requestJson } from '../../../shared/api/httpClient';
import { InferenceSettingsPanel } from '../InferenceSettingsPanel';

vi.mock('../../../shared/api/httpClient', () => ({ requestJson: vi.fn() }));
const settings = {
  llm_provider: 'openai', vlm_provider: 'openai', embedding_provider: 'openai',
  openai_llm_model: 'cloud-llm', openai_vlm_model: 'cloud-vlm', openai_embedding_model: 'cloud-embedding',
  llama_cpp_llm_model: 'qwen3-vl-4b', llama_cpp_vlm_model: 'qwen3-vl-4b', llama_cpp_embedding_model: 'bge-m3',
  llama_cpp_llm_url: 'http://127.0.0.1:8081/v1', llama_cpp_vlm_url: 'http://127.0.0.1:8081/v1', llama_cpp_embedding_url: 'http://127.0.0.1:8083/v1',
  llama_cpp_embedding_dimension: 1024,
};

describe('InferenceSettingsPanel', () => {
  beforeEach(() => { vi.mocked(requestJson).mockReset(); });

  it('saves one local stage while retaining the other cloud stages and explains restart', async () => {
    vi.mocked(requestJson).mockResolvedValueOnce(settings).mockResolvedValueOnce({ saved: true, restart_required: true });
    render(<InferenceSettingsPanel />);
    const providers = await screen.findAllByLabelText('제공자');
    fireEvent.change(providers[0], { target: { value: 'llamacpp' } });
    expect(screen.getByDisplayValue('qwen3-vl-4b')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '모델 설정 저장' }));
    await waitFor(() => expect(requestJson).toHaveBeenLastCalledWith('/api/settings/inference', {
      method: 'PUT', json: { ...settings, llm_provider: 'llamacpp' },
    }));
    expect(await screen.findByRole('status')).toHaveTextContent('FastAPI를 종료한 뒤 다시 실행');
  });

  it('shows a failed save without claiming settings were applied', async () => {
    vi.mocked(requestJson).mockResolvedValueOnce(settings).mockRejectedValueOnce(new Error('저장 실패'));
    render(<InferenceSettingsPanel />);
    await screen.findAllByLabelText('제공자');
    fireEvent.click(screen.getByRole('button', { name: '모델 설정 저장' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('저장 실패');
    expect(screen.queryByText(/저장했습니다/)).not.toBeInTheDocument();
  });
});
