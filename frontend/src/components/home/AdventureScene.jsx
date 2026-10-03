import React from 'react';

// 외부 이미지 없이 해상도에 맞춰 선명하게 표시되는 모험 일러스트.
const AdventureScene = () => (
  <svg viewBox="0 0 480 350" className="adventure-scene" role="img" aria-label="작은 숲에서 함께 모험하는 메이플스토리 슬라임과 주황 버섯">
    <ellipse cx="245" cy="303" rx="177" ry="20" fill="#dce4ce" opacity=".65" />
    <path d="M67 243Q241 215 413 243L386 286Q247 315 95 279Z" fill="#c6ac7b" stroke="#758257" strokeWidth="3" />
    <path d="M69 242Q233 194 415 243Q415 261 390 260Q368 278 348 262Q327 281 306 265Q279 283 255 267Q231 282 207 268Q180 279 158 264Q129 279 111 260Q81 269 69 242" fill="#a8c475" stroke="#758257" strokeWidth="3" strokeLinejoin="round" />
    <path d="M133 294L156 299M326 298L341 295M92 267L104 273" stroke="#ad8e5c" strokeWidth="4" strokeLinecap="round" />
    <g stroke="#769159" strokeWidth="2.5" strokeLinecap="round"><path d="M104 224v-16m0 10-8-7m8 6 8-9M367 226v-19m0 9-8-6m8 9 10-10" /></g>
    <g className="scene-cloud" fill="#fffdf6"><path d="M34 92q-7-20 12-23q8-20 25-6q21-10 26 12q17 1 12 17Z" /><path d="M352 70q-7-17 9-19q8-16 22-6q15-6 20 11q14 2 11 14Z" /></g>
    <circle cx="386" cy="107" r="28" fill="#f4dba0" opacity=".7" />
    {/* 메이플스토리 슬라임의 물방울 몸체와 구슬 달린 줄기. */}
    <defs>
      <radialGradient id="maple-slime-body" cx="38%" cy="31%" r="72%">
        <stop offset="0%" stopColor="#d6fa86" />
        <stop offset="48%" stopColor="#a9e852" />
        <stop offset="82%" stopColor="#7ec237" />
        <stop offset="100%" stopColor="#639d2b" />
      </radialGradient>
      <radialGradient id="maple-slime-orb" cx="34%" cy="28%" r="72%">
        <stop offset="0%" stopColor="#e2fcaa" />
        <stop offset="55%" stopColor="#a9e852" />
        <stop offset="100%" stopColor="#639d2b" />
      </radialGradient>
    </defs>
    <g className="scene-slime">
      <ellipse cx="222" cy="246" rx="69" ry="9" fill="#718b48" opacity=".18" />
      <path d="M214 125C219 100 205 80 185 87C158 96 176 160 155 190Q144 206 136 210" fill="none" stroke="#48652c" strokeWidth="2.2" strokeLinecap="round" />
      <circle cx="135" cy="211" r="8" fill="url(#maple-slime-orb)" stroke="#48652c" strokeWidth="2.5" />
      <ellipse cx="132" cy="208" rx="2.5" ry="2" fill="#f5ffd7" />
      <path d="M214 121C223 139 246 143 263 156C282 170 293 190 291 210C289 233 267 246 224 247C182 248 158 235 154 213C149 190 160 168 181 151C195 140 205 132 214 121Z" fill="url(#maple-slime-body)" stroke="#52752f" strokeWidth="3.5" strokeLinejoin="round" />
      <path d="M168 220C184 237 247 243 275 222" fill="none" stroke="#c7f275" strokeWidth="8" strokeLinecap="round" opacity=".7" />
      <ellipse cx="181" cy="173" rx="12" ry="17" transform="rotate(34 181 173)" fill="#f8ffe2" opacity=".9" />
      <ellipse cx="164" cy="199" rx="5.5" ry="7" transform="rotate(15 164 199)" fill="#f8ffe2" opacity=".8" />
      <ellipse cx="204" cy="195" rx="7.5" ry="9" fill="#31451e" />
      <ellipse cx="252" cy="190" rx="7.5" ry="9" fill="#31451e" />
      <path d="M204 190v10m-4-5h8M252 185v10m-4-5h8" fill="none" stroke="#f4fb79" strokeWidth="2.4" strokeLinecap="round" />
      <path d="M223 203q1 7 6 3q4 5 7-3" fill="none" stroke="#31451e" strokeWidth="2.8" strokeLinecap="round" strokeLinejoin="round" />
    </g>
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
