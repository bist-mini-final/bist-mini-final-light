import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { BiPageNotice } from '../BiPageNotice';

describe('BiPageNotice', () => {
  it('keeps the sample calculation method visible after completion', () => {
    render(<BiPageNotice refresh={{ status: 'idle', jobId: null, startedAt: null, message: '원본 셀에서 직접 계산한 대시보드입니다. LLM 지표 추출 결과가 아닙니다.' }} />);
    expect(screen.getByRole('status')).toHaveTextContent('LLM 지표 추출 결과가 아닙니다.');
  });

  it('does not create a notice for an idle snapshot without a message', () => {
    const { container } = render(<BiPageNotice refresh={{ status: 'idle', jobId: null, startedAt: null, message: null }} />);
    expect(container).toBeEmptyDOMElement();
  });
});
