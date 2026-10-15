import{c as u,r as e}from"./index-CYG-lNEe.js";/**
 * @license lucide-react v0.475.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const f=[["circle",{cx:"12",cy:"12",r:"3",key:"1v7zrd"}],["path",{d:"M3 7V5a2 2 0 0 1 2-2h2",key:"aa7l1z"}],["path",{d:"M17 3h2a2 2 0 0 1 2 2v2",key:"4qcy5o"}],["path",{d:"M21 17v2a2 2 0 0 1-2 2h-2",key:"6vwrx8"}],["path",{d:"M7 21H5a2 2 0 0 1-2-2v-2",key:"ioqczr"}]],C=u("Focus",f);/**
 * @license lucide-react v0.475.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const I=[["path",{d:"M5 12h14",key:"1ays0h"}]],T=u("Minus",I),h='button, a, input, select, textarea, [data-pan-ignore="true"]';function k(c){const a=e.useRef(null),[p,i]=e.useState(!1),s=e.useCallback(r=>{var n,o;const t=a.current;!t||t.pointerId!==r.pointerId||(a.current=null,i(!1),(o=(n=r.currentTarget).hasPointerCapture)!=null&&o.call(n,r.pointerId)&&r.currentTarget.releasePointerCapture(r.pointerId))},[]),d=e.useCallback(r=>{var o,l;if(r.button!==0)return;const t=r.target instanceof Element?r.target:null;if(t!=null&&t.closest(h))return;const n=c.current;n&&(a.current={pointerId:r.pointerId,clientX:r.clientX,clientY:r.clientY,scrollLeft:n.scrollLeft,scrollTop:n.scrollTop},(l=(o=r.currentTarget).setPointerCapture)==null||l.call(o,r.pointerId),r.preventDefault(),i(!0))},[c]),g=e.useCallback(r=>{const t=a.current,n=c.current;!t||!n||t.pointerId!==r.pointerId||(n.scrollLeft=t.scrollLeft-(r.clientX-t.clientX),n.scrollTop=t.scrollTop-(r.clientY-t.clientY))},[c]);return{isDragging:p,dragPanProps:{onPointerDown:d,onPointerMove:g,onPointerUp:s,onPointerCancel:s,onLostPointerCapture:s}}}export{C as F,T as M,k as u};
