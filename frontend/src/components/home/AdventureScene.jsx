import React from 'react';

// 외부 이미지 없이 해상도에 맞춰 선명하게 표시되는 모험 일러스트.
const AdventureScene = () => (
  <svg viewBox="0 0 480 350" className="adventure-scene" role="img" aria-label="작은 숲에서 함께 모험하는 초록 요정과 주황 버섯">
    <ellipse cx="245" cy="303" rx="177" ry="20" fill="#dce4ce" opacity=".65" />
    <path d="M67 243Q241 215 413 243L386 286Q247 315 95 279Z" fill="#c6ac7b" stroke="#758257" strokeWidth="3" />
    <path d="M69 242Q233 194 415 243Q415 261 390 260Q368 278 348 262Q327 281 306 265Q279 283 255 267Q231 282 207 268Q180 279 158 264Q129 279 111 260Q81 269 69 242" fill="#a8c475" stroke="#758257" strokeWidth="3" strokeLinejoin="round" />
    <path d="M133 294L156 299M326 298L341 295M92 267L104 273" stroke="#ad8e5c" strokeWidth="4" strokeLinecap="round" />
    <g stroke="#769159" strokeWidth="2.5" strokeLinecap="round"><path d="M104 224v-16m0 10-8-7m8 6 8-9M367 226v-19m0 9-8-6m8 9 10-10" /></g>
    <g className="scene-cloud" fill="#fffdf6"><path d="M34 92q-7-20 12-23q8-20 25-6q21-10 26 12q17 1 12 17Z" /><path d="M352 70q-7-17 9-19q8-16 22-6q15-6 20 11q14 2 11 14Z" /></g>
    <circle cx="386" cy="107" r="28" fill="#f4dba0" opacity=".7" />
    <path d="M155 190Q152 159 169 148Q149 116 168 99Q184 84 202 95Q224 68 247 101Q276 96 286 119Q297 141 274 157Q297 202 277 228Q224 254 175 229Q155 220 155 190Z" fill="#c1da8d" stroke="#657a44" strokeWidth="3.5" />
    <path d="M178 154Q165 177 174 188" fill="none" stroke="#edf5d3" strokeWidth="9" strokeLinecap="round" />
    <path d="M214 100Q205 66 239 54Q256 85 225 102" fill="#7d9b50" stroke="#657a44" strokeWidth="3" />
    <path d="M222 94l12-24" stroke="#b8cf84" strokeWidth="2.5" strokeLinecap="round" />
    <ellipse cx="195" cy="192" rx="5" ry="7" fill="#3d4931" /><ellipse cx="243" cy="192" rx="5" ry="7" fill="#3d4931" />
    <path d="M210 205q10 11 20 0" fill="none" stroke="#3d4931" strokeWidth="3" strokeLinecap="round" />
    <ellipse cx="182" cy="206" rx="9" ry="5" fill="#edb09a" /><ellipse cx="255" cy="206" rx="9" ry="5" fill="#edb09a" />
    <path d="M188 230q-11 17-20 5M255 231q8 13 18 4" fill="#c1da8d" stroke="#657a44" strokeWidth="3" strokeLinecap="round" />
    <g className="scene-mushroom">
      <path d="M309 208q-6 30 2 36q20 10 40 0q8-9-3-35" fill="#fff0d6" stroke="#916946" strokeWidth="3" />
      <path d="M284 204Q280 166 309 150Q340 132 365 163Q380 182 375 203Q338 222 284 204Z" fill="#efa46b" stroke="#916946" strokeWidth="3" />
      <path d="M293 187q-2-15 10-23q9 5 11 16q-5 11-21 7M342 152q12 3 17 13q-4 10-16 8q-7-11-1-21" fill="#fff5df" />
      <circle cx="320" cy="230" r="3" fill="#624a36" /><circle cx="341" cy="230" r="3" fill="#624a36" />
      <path d="M327 237q4 4 7 0" fill="none" stroke="#624a36" strokeWidth="2" strokeLinecap="round" />
    </g>
    <g fill="#ebbb62"><path d="m112 119 4 10 10 4-10 4-4 10-4-10-10-4 10-4Z" /><path d="m313 83 3 7 7 3-7 3-3 7-3-7-7-3 7-3Z" /><circle cx="411" cy="179" r="4" /><circle cx="74" cy="170" r="3" /></g>
    <g fill="#fff8de" stroke="#bdad6c" strokeWidth="2"><path d="M115 250v-12m-6 6h12" /><path d="M372 248v-12m-6 6h12" /></g>
  </svg>
);
export default AdventureScene;
