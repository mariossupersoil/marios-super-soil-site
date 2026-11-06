
const MONTHS=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const POT_SIZES=[1,2,3,5,7,10,15,20,25,30,45,65];

// lastFrost / firstFrost = 0-indexed month number (May=4, Oct=9, etc.)
const ZONES={
  bc_coast:{label:'BC Coastal · Zone 8',        lf:1, ff:10, gw:38},
  bc_int:  {label:'BC Interior · Zone 4–6',     lf:3, ff:9,  gw:26},
  ab:      {label:'Alberta · Zone 3–4',          lf:4, ff:8,  gw:20},
  sk:      {label:'Saskatchewan · Zone 2–3',     lf:4, ff:8,  gw:18},
  mb:      {label:'Manitoba · Zone 2–3',         lf:4, ff:8,  gw:18},
  on_sw:   {label:'Ontario SW · Zone 6–7',       lf:3, ff:9,  gw:28},
  on_gta:  {label:'Ontario GTA/Niagara · Zone 5–6', lf:3, ff:9, gw:26},
  on_ne:   {label:'Ontario North/East · Zone 4–5', lf:4, ff:9, gw:22},
  on_fn:   {label:'Ontario Far North · Zone 2–3', lf:4, ff:8, gw:16},
  qc_s:    {label:'Québec South · Zone 4–5',     lf:4, ff:9,  gw:22},
  qc_n:    {label:'Québec North · Zone 2–3',     lf:5, ff:8,  gw:14},
  ns_nb:   {label:'NS / NB · Zone 5–6',          lf:3, ff:9,  gw:26},
  pei:     {label:'PEI · Zone 6',                lf:3, ff:9,  gw:26},
  nl:      {label:'Newfoundland · Zone 4–5',     lf:4, ff:9,  gw:22},
  us3:     {label:'USA Zone 3',                  lf:4, ff:8,  gw:18},
  us4:     {label:'USA Zone 4',                  lf:4, ff:8,  gw:20},
  us5:     {label:'USA Zone 5',                  lf:3, ff:9,  gw:24},
  us6:     {label:'USA Zone 6',                  lf:3, ff:9,  gw:28},
  us7:     {label:'USA Zone 7',                  lf:2, ff:9,  gw:32},
  us8:     {label:'USA Zone 8',                  lf:1, ff:10, gw:38},
  us9:     {label:'USA Zone 9+',                 lf:0, ff:11, gw:48},
};

// Plant cycle profiles
// type: annual-warm | annual-cool | annual-fall | perennial | cannabis | indoor | lawn
const PROFILES={
  tomato:        {type:'annual-warm', vw:6,  fw:10, hw:2, label:'Vegetative','flower':'Fruiting'},
  pepper:        {type:'annual-warm', vw:6,  fw:10, hw:2},
  cucumber:      {type:'annual-warm', vw:4,  fw:7,  hw:2},
  squash:        {type:'annual-warm', vw:5,  fw:9,  hw:2},
  bean:          {type:'annual-warm', vw:4,  fw:6,  hw:2},
  corn:          {type:'annual-warm', vw:6,  fw:6,  hw:1},
  sunflower:     {type:'annual-warm', vw:5,  fw:6,  hw:2},
  petunia:       {type:'annual-warm', vw:3,  fw:14, hw:0},
  raised_bed:    {type:'annual-warm', vw:6,  fw:10, hw:2},
  lettuce:       {type:'annual-cool', vw:4,  fw:4,  hw:1},
  carrot:        {type:'annual-cool', vw:6,  fw:0,  hw:2},
  brassica:      {type:'annual-cool', vw:6,  fw:4,  hw:2},
  garlic:        {type:'annual-fall', vw:28, fw:4,  hw:2},
  strawberry:    {type:'perennial',   vw:4,  fw:8,  hw:4},
  blueberry:     {type:'perennial',   vw:2,  fw:8,  hw:4},
  raspberry:     {type:'perennial',   vw:2,  fw:8,  hw:6},
  rose:          {type:'perennial',   vw:4,  fw:20, hw:0},
  lavender:      {type:'perennial',   vw:4,  fw:8,  hw:2},
  perennial:     {type:'perennial',   vw:4,  fw:12, hw:2},
  fruit_tree:    {type:'perennial',   vw:4,  fw:16, hw:4},
  ornamental:    {type:'perennial',   vw:4,  fw:8,  hw:0},
  cannabis_veg:  {type:'cannabis',    vw:8,  fw:0,  hw:0},
  cannabis_flower:{type:'cannabis',   vw:0,  fw:9,  hw:1},
  cannabis_full: {type:'cannabis',    vw:8,  fw:9,  hw:1},
  tropical:      {type:'indoor'},
  succulent:     {type:'indoor'},
  orchid:        {type:'indoor'},
  lawn:          {type:'lawn'},
};

function clampMonth(m){ return Math.max(0, Math.min(11, m)); }
function wksToMonths(w){ return Math.round(w/4.33); }

function buildCycleInfo(plantKey, zoneKey, customVeg, customFlower){
  const pr = PROFILES[plantKey];
  if(!pr) return null;
  if(pr.type==='indoor') return {type:'indoor'};
  if(pr.type==='lawn') return {type:'lawn'};

  const isCustom = !zoneKey;
  const z = zoneKey ? ZONES[zoneKey] : null;
  const vw = parseInt(customVeg)||pr.vw;
  const fw = parseInt(customFlower)||pr.fw;
  const hw = pr.hw||0;

  if(isCustom){
    return {type:'custom', vw, fw, hw, total:vw+fw+hw};
  }

  const bar = Array(12).fill('cal-off');
  let lines=[], timingA, timingB, timingC;

  if(pr.type==='annual-warm'){
    // Plant after last frost
    const ps = clampMonth(z.lf + 1);
    const ve = clampMonth(ps + wksToMonths(vw));
    const fe = clampMonth(ve + wksToMonths(fw));
    const he = clampMonth(fe + wksToMonths(hw));
    for(let m=0;m<12;m++){
      if(m===ps) bar[m]='cal-prep';
      else if(m>ps && m<ve) bar[m]='cal-veg';
      else if(m===ve && fw>0) bar[m]='cal-trans';
      else if(m>ve && m<=fe && fw>0) bar[m]='cal-flower';
      else if(m>fe && m<=he && hw>0) bar[m]='cal-harvest';
    }
    const frostWarn = he >= z.ff;
    lines=[
      `📌 <strong>Transplant outdoors:</strong> ${MONTHS[ps]} (after last frost in ${MONTHS[z.lf]})`,
      `🌱 <strong>Vegetative / establishment:</strong> ${MONTHS[ps]}–${MONTHS[ve]} (~${vw} weeks)`,
      fw>0 ? `🌸 <strong>Flowering / fruiting:</strong> ${MONTHS[ve]}–${MONTHS[fe]} (~${fw} weeks)` : null,
      hw>0 ? `🌾 <strong>Harvest window:</strong> ${MONTHS[fe]}–${MONTHS[he]}` : null,
      frostWarn ? `⚠️ Tight on time — first frost expected ${MONTHS[z.ff]}. Start transplants indoors 6–8 weeks before last frost or choose early-maturing varieties.` :
                  `✅ Harvest completes before first frost (${MONTHS[z.ff]}) — you have good time.`,
    ];
    timingA={num:`${vw}w`, lbl:'Veg / Establish'};
    timingB=fw>0?{num:`${fw}w`, lbl:'Flower / Fruit'}:null;
    timingC={num:`${z.gw}w`, lbl:'Total Season'};
  }

  else if(pr.type==='annual-cool'){
    // Cool crops: plant at or slightly before last frost
    const ps = clampMonth(z.lf);
    const ve = clampMonth(ps + wksToMonths(vw));
    const fe = clampMonth(ve + wksToMonths(fw));
    const he = clampMonth(fe + wksToMonths(hw));
    for(let m=0;m<12;m++){
      if(m===ps) bar[m]='cal-prep';
      else if(m>ps && m<ve) bar[m]='cal-veg';
      else if(m>=ve && m<fe && fw>0) bar[m]='cal-flower';
      else if(m>=fe && m<=he && hw>0) bar[m]='cal-harvest';
    }
    lines=[
      `📌 <strong>Direct sow / transplant:</strong> ${MONTHS[ps]} — cool-season crops tolerate light frost`,
      `🌱 <strong>Growing period:</strong> ${MONTHS[ps]}–${MONTHS[he]} (~${vw+fw+hw} weeks total)`,
      `💡 For a fall harvest, also plant in ${MONTHS[Math.max(0,z.ff-Math.round((vw+fw+hw)/4.33))]} for harvest before first frost (${MONTHS[z.ff]})`,
    ];
    timingA={num:`${vw+fw+hw}w`, lbl:'Grow Cycle'};
    timingB={num:MONTHS[ps], lbl:'Plant Date'};
    timingC={num:MONTHS[he]||MONTHS[clampMonth(ps+wksToMonths(vw+fw+hw))], lbl:'Harvest'};
  }

  else if(pr.type==='annual-fall'){
    // Garlic: plant in fall
    const ps = clampMonth(z.ff - 1);
    const springStart = clampMonth(z.lf + 1);
    const harvest = clampMonth(springStart + 3);
    for(let m=0;m<12;m++){
      if(m===ps) bar[m]='cal-prep';
      else if(m>ps || m<=1) bar[m]='cal-dormant';
      else if(m>=springStart && m<harvest) bar[m]='cal-veg';
      else if(m===harvest) bar[m]='cal-harvest';
    }
    lines=[
      `📌 <strong>Plant in fall:</strong> ${MONTHS[ps]} — garlic needs a cold period to form bulbs`,
      `❄️ <strong>Overwinters</strong> under mulch — apply amendments at planting in ${MONTHS[ps]}`,
      `🌱 <strong>Spring growth resumes:</strong> ${MONTHS[springStart]}`,
      `🌾 <strong>Harvest:</strong> ${MONTHS[harvest]} when leaves are ~50% yellow and falling over`,
    ];
    timingA={num:MONTHS[ps], lbl:'Plant (Fall)'};
    timingB={num:MONTHS[springStart], lbl:'Spring Growth'};
    timingC={num:MONTHS[harvest], lbl:'Harvest'};
  }

  else if(pr.type==='perennial'){
    const active = clampMonth(z.lf + 1);
    const flowerS = clampMonth(active + wksToMonths(vw));
    const flowerE = clampMonth(flowerS + wksToMonths(fw));
    const harvestE = clampMonth(flowerE + wksToMonths(hw));
    for(let m=0;m<12;m++){
      if(m>=active && m<flowerS) bar[m]='cal-veg';
      else if(m>=flowerS && m<=flowerE && fw>0) bar[m]='cal-flower';
      else if(m>flowerE && m<=harvestE && hw>0) bar[m]='cal-harvest';
      else if(m<active || m>harvestE) bar[m]='cal-dormant';
    }
    lines=[
      `🌿 <strong>Active growth resumes:</strong> ${MONTHS[active]} in ${z.label}`,
      `📌 <strong>Best time to apply amendments:</strong> ${MONTHS[active]} (spring) and ${MONTHS[Math.max(0,z.ff-1)]} (fall)`,
      fw>0 ? `🌸 <strong>Bloom / fruiting window:</strong> ${MONTHS[flowerS]}–${MONTHS[flowerE]}` : null,
      hw>0 ? `🌾 <strong>Harvest window:</strong> ${MONTHS[flowerE]}–${MONTHS[harvestE]}` : null,
      `❄️ <strong>Goes dormant around:</strong> ${MONTHS[z.ff]} — apply fall amendments in ${MONTHS[Math.max(0,z.ff-1)]}`,
    ];
    timingA={num:MONTHS[active], lbl:'Active Growth'};
    timingB=fw>0?{num:`${MONTHS[flowerS]}–${MONTHS[flowerE]}`, lbl:'Bloom/Fruit'}:null;
    timingC={num:`${z.gw}w`, lbl:'Growing Season'};
  }

  else if(pr.type==='cannabis'){
    // Outdoor cannabis flips to flower when days shorten ~Aug
    const vegStart = clampMonth(z.lf + 2); // usually May/June
    const flowerFlip = 7; // August — natural photoperiod trigger
    const actualVegWks = Math.round((flowerFlip - vegStart) * 4.33);
    const harvestEnd = clampMonth(flowerFlip + wksToMonths(fw + hw));
    for(let m=0;m<12;m++){
      if(m===vegStart-1) bar[m]='cal-prep';
      else if(m>=vegStart && m<flowerFlip) bar[m]='cal-veg';
      else if(m===flowerFlip) bar[m]='cal-trans';
      else if(m>flowerFlip && m<harvestEnd) bar[m]='cal-flower';
      else if(m===harvestEnd) bar[m]='cal-harvest';
    }
    const tightSeason = harvestEnd >= z.ff;
    lines=[
      `📌 <strong>Transplant outdoors:</strong> ${MONTHS[vegStart]} after last frost (${MONTHS[z.lf]})`,
      `🌱 <strong>Vegetative phase:</strong> ${MONTHS[vegStart]}–${MONTHS[flowerFlip-1]} (~${actualVegWks} weeks) — apply Level Up &amp; Feather Meal`,
      `🌸 <strong>Natural flip to flower:</strong> ${MONTHS[flowerFlip]} as days shorten — switch to Flower Power &amp; Bone Meal`,
      `🌾 <strong>Harvest window:</strong> ${MONTHS[Math.max(0,harvestEnd-1)]}–${MONTHS[harvestEnd]}`,
      tightSeason ? `⚠️ First frost expected ${MONTHS[z.ff]} — choose strains with <strong>${fw} weeks or less</strong> flower time. Auto-flowering strains are recommended for zones 4 and colder.` :
                    `✅ Harvest completes before first frost (${MONTHS[z.ff]}) with time to spare.`,
    ];
    timingA={num:`${actualVegWks}w`, lbl:'Veg (outdoor)'};
    timingB={num:`${fw}w`, lbl:'Flower'};
    timingC={num:MONTHS[harvestEnd], lbl:'Harvest'};
  }

  // Legend: only include colors actually used
  const usedClasses = new Set(bar);
  const LEGEND=[
    {cls:'cal-prep',    color:'#8bc4a8', lbl:'Prep / Plant'},
    {cls:'cal-veg',     color:'#2d7a4a', lbl:'Veg / Establish'},
    {cls:'cal-trans',   color:'#e67e22', lbl:'Transition'},
    {cls:'cal-flower',  color:'#d35400', lbl:'Flower / Fruit'},
    {cls:'cal-harvest', color:'#c0392b', lbl:'Harvest'},
    {cls:'cal-grow',    color:'#1a5276', lbl:'Active Growth'},
    {cls:'cal-dormant', color:'#bbb',    lbl:'Dormant / Off'},
  ].filter(l=>usedClasses.has(l.cls));

  return {
    type: pr.type,
    zoneLabel: z.label,
    bar, lines: lines.filter(Boolean), LEGEND,
    timingA, timingB, timingC,
    lastFrost: MONTHS[z.lf],
    firstFrost: MONTHS[z.ff],
    growWeeks: z.gw,
    vw, fw, hw,
  };
}

function renderCycleBlock(info){
  if(!info || info.type==='indoor') return '<div style="font-size:13px;color:#888;padding:.5rem 0">This plant grows year-round indoors — no seasonal cycle applies. Use the Custom tab to track your own schedule.</div>';
  if(info.type==='lawn') return '<div style="font-size:13px;color:#888;padding:.5rem 0">Apply Level Up and Compost in early spring and again in fall, regardless of zone. Water in thoroughly.</div>';

  if(info.type==='custom'){
    const parts=[];
    if(info.vw) parts.push(`🌱 <strong>Veg / Establish:</strong> ${info.vw} weeks`);
    if(info.fw) parts.push(`🌸 <strong>Flower / Fruit:</strong> ${info.fw} weeks`);
    if(info.total) parts.push(`📅 <strong>Total cycle:</strong> ${info.total} weeks`);
    return `<div class="zone-result"><div class="zone-summary">${parts.join('<br>')}</div><p style="font-size:11px;color:#999">Select a region in the Outdoor tab to see a full monthly calendar.</p></div>`;
  }

  const barHtml = info.bar.map((cls,i)=>
    `<div class="cal-month ${cls}" title="${MONTHS[i]}">${MONTHS[i]}</div>`
  ).join('');

  const legendHtml = info.LEGEND.map(l=>
    `<div class="cal-leg-item"><div class="cal-leg-dot" style="background:${l.color}"></div>${l.lbl}</div>`
  ).join('');

  const timingHtml = [info.timingA, info.timingB, info.timingC].filter(Boolean).map(t=>
    `<div class="timing-box"><div class="timing-num">${t.num}</div><div class="timing-lbl">${t.lbl}</div></div>`
  ).join('');

  return `<div class="zone-result">
    <div class="zone-summary">${info.lines.join('<br>')}</div>
    <div class="calendar-bar">${barHtml}</div>
    <div class="cal-legend">${legendHtml}</div>
    <div class="timing-row">${timingHtml}</div>
    <div class="zone-foot">❄️ <strong>Last frost:</strong> ${info.lastFrost} &nbsp;·&nbsp; <strong>First frost:</strong> ${info.firstFrost} &nbsp;·&nbsp; <strong>Growing season:</strong> ~${info.growWeeks} weeks</div>
  </div>`;
}

// ── Products ──
const PRODUCTS={
  // lbs100 = lbs per 100 sqft at standard 6-inch amendment depth (industry rates)
  // tbsp   = tablespoons per gallon of pot volume (container rate)
  levelUp:    {name:'Level Up 3-3-3',       npk:'3-3-3',    url:'https://mariossupersoil.ca/level-up-organic-gardening',   tbsp:1.0,  lbs100:2.0},
  flowerPower:{name:'Flower Power 2-6-4',   npk:'2-6-4',    url:'https://mariossupersoil.ca/flower-power-2-6-4',          tbsp:1.0,  lbs100:2.0},
  featherMeal:{name:'Feather Meal 11-0-0',  npk:'11-0-0',   url:'https://mariossupersoil.ca/sustainable-fertilizers',     tbsp:1.0,  lbs100:1.0},
  boneMeal:   {name:'Bone Meal 4-10-0',     npk:'4-10-0',   url:'https://mariossupersoil.ca/sustainable-fertilizers',     tbsp:1.0,  lbs100:2.0},
  bloodMeal:  {name:'Blood Meal 12-0-0',    npk:'12-0-0',   url:'https://mariossupersoil.ca/sustainable-fertilizers',     tbsp:0.5,  lbs100:0.75},
  kelpMeal:   {name:'Kelp Meal 1-0-4',      npk:'1-0-4',    url:'https://mariossupersoil.ca/kelp-meal',                   tbsp:1.0,  lbs100:1.5},
  alfalfa:    {name:'Alfalfa Meal 3-0.5-3', npk:'3-0.5-3',  url:'https://mariossupersoil.ca/sustainable-fertilizers',     tbsp:2.0,  lbs100:2.0},
  insectFrass:{name:'Insect Frass 3-1-3',   npk:'3-1-3',    url:'https://mariossupersoil.ca/sustainable-fertilizers',     tbsp:0.75, lbs100:1.5},
  crabMeal:   {name:'Crab Meal 4-3-0',      npk:'4-3-0',    url:'https://mariossupersoil.ca/sustainable-fertilizers',     tbsp:0.33, lbs100:2.0},
  kmag:       {name:'K-Mag 0-0-22',         npk:'0-0-22',   url:'https://mariossupersoil.ca/marios-super-soil-k-mag',     tbsp:0.5,  lbs100:1.0},
  softRockP:  {name:'Soft Rock Phosphate',  npk:'0-3-0',    url:'https://mariossupersoil.ca/sustainable-fertilizers',     tbsp:1.0,  lbs100:3.0},
  basalt:     {name:'Basalt Rock Dust',      npk:'minerals', url:'https://mariossupersoil.ca/sustainable-fertilizers',     tbsp:1.0,  lbs100:5.0},
  dolomite:   {name:'Dolomite Lime',         npk:'Ca/Mg',    url:'https://mariossupersoil.ca/sustainable-fertilizers',     tbsp:1.0,  lbs100:5.0},
  gypsum:     {name:'Gypsum',                npk:'Ca/S',     url:'https://mariossupersoil.ca/sustainable-fertilizers',     tbsp:0.75, lbs100:2.0},
  glacialRock:{name:'Glacial Rock Dust',     npk:'minerals', url:'https://mariossupersoil.ca/sustainable-fertilizers',     tbsp:1.0,  lbs100:5.0},
  zeolite:    {name:'Zeolite',               npk:'retention',url:'https://mariossupersoil.ca/sustainable-fertilizers',     tbsp:1.0,  lbs100:2.0},
  azomite:    {name:'Azomite',               npk:'minerals', url:'https://mariossupersoil.ca/sustainable-fertilizers',     tbsp:0.5,  lbs100:1.0},
  humicAcid:  {name:'Humic Acid (Granular)', npk:'bio',      url:'https://mariossupersoil.ca/sustainable-fertilizers',     tbsp:0.25, lbs100:0.5},
  wormCast:   {name:'Worm Castings',         npk:'1.5-2.5-1.3',url:'https://mariossupersoil.ca/worm-castings',            tbsp:2.0,  lbs100:5.0},
  biochar:    {name:'Biochar (Charged)',      npk:'carbon',   url:'https://mariossupersoil.ca/sustainable-fertilizers',     tbsp:1.0,  lbs100:2.0},
  karanja:    {name:'Karanja Cake',          npk:'pest/fert',url:'https://mariossupersoil.ca/sustainable-fertilizers',     tbsp:0.5,  lbs100:1.0},
  compost:    {name:'Compost Blend',         npk:'organic',  url:'https://mariossupersoil.ca/sustainable-fertilizers',     tbsp:2.0,  lbs100:5.0},
  fishCompost:{name:'Fish Compost',          npk:'organic/N',url:'https://mariossupersoil.ca/sustainable-fertilizers',     tbsp:1.5,  lbs100:3.0},
  yucca:      {name:'Yucca Powder ThermX',   npk:'wetting',  url:'https://mariossupersoil.ca/sustainable-fertilizers',     tbsp:0.25, lbs100:0.25},
  maltedBarley:{name:'Malted Barley Flour',  npk:'enzymes',  url:'https://mariossupersoil.ca/sustainable-fertilizers',     tbsp:0.5,  lbs100:0.5},
  pumice:     {name:'Pumice 3/8',            npk:'aeration', url:'https://mariossupersoil.ca/sustainable-fertilizers',     tbsp:2.0,  lbs100:5.0},
  oysterShell:{name:'Oyster Shell Flour',    npk:'Ca',       url:'https://mariossupersoil.ca/sustainable-fertilizers',     tbsp:1.0,  lbs100:2.0},
};

const PLANTS={
  tomato:{name:'Tomatoes',note:'Heavy feeders that need strong veg growth AND high P/K for fruit set.',tip:'Apply essentials at planting. Top dress with Level Up monthly. Switch to Flower Power and Bone Meal at first flower.',essential:[{p:'levelUp',why:'Balanced all-purpose base amendment for the full season'},{p:'flowerPower',why:'High P/K drives fruit set, size, and flavour'},{p:'wormCast',why:'Living biology that feeds roots gently all season long'}],recommended:[{p:'kelpMeal',why:'Plant hormones and micronutrients boost stress tolerance and fruit quality'},{p:'boneMeal',why:'Slow-release phosphorus for bigger fruit development'},{p:'humicAcid',why:'Dramatically improves nutrient uptake and root growth'}],optional:[{p:'alfalfa',why:'Triacontanol in alfalfa accelerates growth and cell division'},{p:'insectFrass',why:'Chitosan triggers immune response and adds balanced NPK'},{p:'fishCompost',why:'Rich organic matter and nitrogen for heavy feeding phases'},{p:'basalt',why:'Slow-release minerals and silica for stronger cell walls'}],starterReason:"Tomatoes are the ultimate heavy feeder. The Super Starter Pack gets you the core kit; add Bone Meal and Feather Meal for maximum yields."},
  pepper:{name:'Peppers & Chili',note:'Medium feeders that love phosphorus for flavour and heat development.',tip:'Level Up at transplant, Flower Power when buds appear. Light Kelp Meal top dress monthly.',essential:[{p:'levelUp',why:'All-purpose base for vigorous plant structure'},{p:'flowerPower',why:'Phosphorus drives capsaicin production and big fruits'},{p:'kelpMeal',why:'Stress hormones help peppers handle heat — critical for Canadian summers'}],recommended:[{p:'wormCast',why:'Gentle biology that prevents transplant shock'},{p:'boneMeal',why:'Slow-release P for sustained fruiting'}],optional:[{p:'alfalfa',why:'Triacontanol boosts cell division during fruiting'},{p:'humicAcid',why:'Improves uptake of phosphorus for maximum heat and flavour'},{p:'fishCompost',why:'Adds organic matter and nitrogen during veg phase'}],starterReason:"Peppers love the full organic program. The Super Starter Pack covers everything — just add extra Bone Meal if you want max heat and flavour."},
  cucumber:{name:'Cucumbers & Zucchini',note:'Fast growing, high water demand vines that need steady nutrition.',tip:'Top dress every 3 weeks. Add K-Mag when fruits start sizing.',essential:[{p:'levelUp',why:'Fast-release balanced nutrition for rapid vine growth'},{p:'flowerPower',why:'Phosphorus and potassium for heavy fruit production'},{p:'kelpMeal',why:'Micronutrients reduce bitterness and improve flavour'}],recommended:[{p:'wormCast',why:'Living soil biology supports the massive nutrient demand'},{p:'kmag',why:'Magnesium and potassium improve fruit sweetness and crunch'}],optional:[{p:'alfalfa',why:'Speeds up veg growth for earlier harvests'},{p:'gypsum',why:'Calcium prevents blossom end rot in cucumbers'},{p:'humicAcid',why:'Improves moisture retention important for cucumbers'}],starterReason:"Cucumbers are heavy drinkers and feeders — the Super Starter Pack gives you the full amendment stack at the best price."},
  lettuce:{name:'Lettuce & Greens',note:'Light feeders that prefer gentle, balanced nutrition. Avoid high nitrogen which causes bolting.',tip:'One light application at planting is usually enough. Worm castings are perfect for leafy greens.',essential:[{p:'wormCast',why:'Perfectly gentle nutrition for leafy greens — no burn risk'},{p:'levelUp',why:'Light balanced amendment for the full season'}],recommended:[{p:'kelpMeal',why:'Micronutrients for deep colour and nutrition density'},{p:'humicAcid',why:'Improves nutrient uptake without pushing excessive growth'},{p:'compost',why:'Rich organic matter for moisture retention and biology'}],optional:[{p:'glacialRock',why:'Slow-release minerals improve leaf nutrient density'},{p:'fishCompost',why:'Low-level organic nitrogen for consistent steady growth'}],starterReason:"For lettuce alone, Worm Castings and Level Up are all you need — but the Starter Pack covers your whole garden."},
  carrot:{name:'Root Vegetables (Carrots, Beets)',note:'Root crops need deep, loose soil with moderate nutrition. Too much nitrogen causes hairy forked roots.',tip:'Work amendments 12 inches deep before planting. Worm Castings mixed into the backfill makes a big difference for root development.',essential:[{p:'levelUp',why:'Low-nitrogen balanced base at a reduced rate encourages root development'},{p:'basalt',why:'Slow-release minerals encourage deep root exploration'}],recommended:[{p:'boneMeal',why:'Phosphorus encourages strong root development without excess nitrogen'},{p:'gypsum',why:'Calcium and sulfur improve soil structure for straight, long roots'},{p:'wormCast',why:'Gentle biology improves soil texture and drainage'}],optional:[{p:'kelpMeal',why:'Auxins in kelp promote root cell elongation'},{p:'glacialRock',why:'Broad mineral spectrum improves flavour and nutrition of root crops'},{p:'humicAcid',why:'Humic acid chelates minerals making them available deeper in the soil'}],starterReason:"The Starter Pack gives you Level Up, Kelp Meal, Worm Castings, Alfalfa Meal, and Compost — everything root crops need to thrive."},
  squash:{name:'Squash & Pumpkins',note:'Heavy feeders with massive nutrient demand. These plants will eat as much as you give them.',tip:'Top dress monthly with Level Up. Add Flower Power, Bone Meal, and K-Mag when fruits set.',essential:[{p:'levelUp',why:'High-volume balanced feeding for enormous vegetative growth'},{p:'flowerPower',why:'High P/K for large, dense fruit development'},{p:'kelpMeal',why:'Micronutrients and stress hormones for the long growing season'}],recommended:[{p:'boneMeal',why:'Phosphorus for fruit size and seed development'},{p:'wormCast',why:'Living biology supports the heavy feeding demand'},{p:'kmag',why:'Potassium and magnesium for fruit sweetness and storage life'}],optional:[{p:'alfalfa',why:'Accelerates vine growth and cell division'},{p:'fishCompost',why:'Nitrogen-rich compost feeds heavy veg phase'},{p:'insectFrass',why:'Chitosan triggers disease resistance in sprawling vines'},{p:'humicAcid',why:'Improves nutrient uptake across the wide root zone'}],starterReason:"Squash and pumpkins are the hungriest plants in your garden. The Super Starter Pack is the best value base — add Bone Meal and K-Mag for giant fruits."},
  bean:{name:'Beans & Peas',note:'Legumes fix their own nitrogen. Focus on soil biology and minerals, not NPK.',tip:'Mix Worm Castings and Compost into the planting area. Focus on soil biology and minerals, not high nitrogen.',essential:[{p:'wormCast',why:'Biology and gentle nutrition without competing with nitrogen fixation'},{p:'kelpMeal',why:'Micronutrients and potassium for pod development and flavour'}],recommended:[{p:'basalt',why:'Broad mineral spectrum supports the nitrogen-fixing process'},{p:'boneMeal',why:'Phosphorus is essential for nitrogen fixation — often overlooked'},{p:'glacialRock',why:'Trace minerals improve yield and nutritional quality'}],optional:[{p:'humicAcid',why:'Improves soil structure and nutrient availability'},{p:'gypsum',why:'Calcium and sulfur support root nodule formation'},{p:'compost',why:'Organic matter feeds soil biology without excess nitrogen'}],starterReason:"The Kelp Meal, Worm Castings, and Compost in the Starter Pack supercharge the soil biology that legumes depend on for nitrogen fixation."},
  corn:{name:'Corn',note:'One of the heaviest nitrogen feeders. Needs abundant nitrogen in veg and P/K at tasseling.',tip:'Side dress with Blood Meal or Feather Meal at knee-high stage. Switch to Flower Power and K-Mag at tasseling.',essential:[{p:'levelUp',why:'All-purpose base to start the season'},{p:'featherMeal',why:'Slow-release 11% nitrogen feeds corn through the full veg phase'},{p:'flowerPower',why:'P/K for tassel development, pollination, and kernel fill'}],recommended:[{p:'bloodMeal',why:'Fast-acting nitrogen for side-dressing at knee-high stage'},{p:'kelpMeal',why:'Stress resistance during hot dry periods'},{p:'kmag',why:'Potassium and magnesium for kernel development and sweetness'},{p:'wormCast',why:'Biology improves nitrogen efficiency'}],optional:[{p:'basalt',why:'Silica strengthens stalks against lodging in wind'},{p:'fishCompost',why:'Organic nitrogen and biology for heavy feeding phases'}],starterReason:"Corn is a nitrogen powerhouse — the Starter Pack is a great foundation. Add Feather Meal and Blood Meal for maximum ear development."},
  brassica:{name:'Brassicas (Kale, Broccoli, Cabbage)',note:'Heavy nitrogen feeders. Also very sensitive to pH — keep it 6.5–7.0.',tip:'Apply Dolomite Lime if pH is below 6.5. Top dress with Feather Meal at 4 weeks.',essential:[{p:'levelUp',why:'Balanced base amendment for strong plant structure'},{p:'featherMeal',why:'High nitrogen feeds the heavy leaf and head development'},{p:'dolomite',why:'Corrects pH and provides calcium and magnesium — critical for brassicas'}],recommended:[{p:'wormCast',why:'Biology and gentle nutrition support disease resistance'},{p:'kelpMeal',why:'Micronutrients improve colour, density, and nutrition'},{p:'insectFrass',why:'Chitosan triggers brassica immune defenses against caterpillars and aphids'}],optional:[{p:'boneMeal',why:'Phosphorus for root development and head formation'},{p:'gypsum',why:'Calcium without raising pH for heavy brassica feeders'}],starterReason:"Brassicas need the full soil biology support that comes with the Starter Pack. Worm Castings and Kelp Meal are especially impactful."},
  garlic:{name:'Garlic & Onions',note:'Bulb crops that build size through consistent steady feeding. Plant in fall for spring harvest.',tip:'Apply amendments at planting in fall. Top dress lightly in spring as shoots emerge. Rich compost at planting gives bulbs the organic matter they need to size up.',essential:[{p:'levelUp',why:'Balanced nutrition through the full growing cycle'},{p:'boneMeal',why:'Phosphorus drives bulb development and size'}],recommended:[{p:'kelpMeal',why:'Potassium and micronutrients improve flavour and storage life'},{p:'wormCast',why:'Gentle biology in the root zone where bulbs form'},{p:'gypsum',why:'Sulfur improves the sulphur compounds that give garlic its flavour'}],optional:[{p:'basalt',why:'Slow-release minerals improve flavour complexity'},{p:'fishCompost',why:'Organic matter and nitrogen for strong spring growth'},{p:'humicAcid',why:'Chelates minerals making them available as temperatures drop in fall'}],starterReason:"The Starter Pack covers every core amendment garlic needs — Level Up, Kelp Meal, Worm Castings, Alfalfa Meal, and Compost for rich organic matter."},
  strawberry:{name:'Strawberries',note:'Perennial fruiting plants that need balanced feeding to build runners AND high P/K for berry production.',tip:'Apply Level Up and Bone Meal in early spring. Add Flower Power and K-Mag as berries develop.',essential:[{p:'levelUp',why:'Balanced base for runner and crown development'},{p:'flowerPower',why:'High P/K for berry production and sweetness'},{p:'wormCast',why:'Living biology in the bed improves flavour and berry nutrition'}],recommended:[{p:'boneMeal',why:'Phosphorus for root and berry development'},{p:'kelpMeal',why:'Potassium and micronutrients improve sweetness and shelf life'}],optional:[{p:'gypsum',why:'Calcium prevents tip burn and improves berry firmness'},{p:'fishCompost',why:'Organic nitrogen for establishment year'},{p:'kmag',why:'Potassium and magnesium for maximum berry sweetness'}],starterReason:"Strawberries are long-term plants — the Starter Pack sets up the soil ecosystem that gets better every year."},
  blueberry:{name:'Blueberries',note:'Acid-loving shrubs that need pH 4.5–5.5. Use sulfur to lower pH if needed. Avoid lime.',tip:'Annual top dressing in spring. These are 20-year plants — invest in the soil biology early.',essential:[{p:'levelUp',why:'Low pH compatible balanced base'},{p:'kelpMeal',why:'Potassium and micronutrients that blueberries need in acidic soil'},{p:'wormCast',why:'Biology and gentle nutrition suited to acidic conditions'}],recommended:[{p:'flowerPower',why:'P/K for berry yield and fruit quality'},{p:'humicAcid',why:'Improves nutrient availability in low-pH acidic soils'},{p:'fishCompost',why:'Acidic organic matter that lowers pH while feeding'}],optional:[{p:'azomite',why:'Broad mineral spectrum improves berry flavour complexity'},{p:'basalt',why:'Slow-release minerals without raising pH'},{p:'biochar',why:'Improves water and nutrient retention in the acid root zone'}],starterReason:"Blueberries are long-term investments — the Starter Pack builds the soil biology and organic matter that pays dividends for the entire 20+ year life of the plant."},
  raspberry:{name:'Raspberries & Blackberries',note:'Cane fruits that produce for 10+ years. Invest in soil biology early for long-term returns.',tip:'Apply Level Up and Bone Meal in early spring. Add Flower Power as canes begin to flower.',essential:[{p:'levelUp',why:'All-purpose feeding for strong cane development'},{p:'flowerPower',why:'Phosphorus and potassium for fruit yield and flavour'},{p:'wormCast',why:'Long-term biology investment for perennial beds'}],recommended:[{p:'boneMeal',why:'Phosphorus builds the fruiting canes'},{p:'kelpMeal',why:'Stress resistance for cold Canadian winters'}],optional:[{p:'alfalfa',why:'Triacontanol stimulates vigorous new cane growth each spring'},{p:'fishCompost',why:'Organic nitrogen and biology for establishment'},{p:'basalt',why:'Minerals improve berry colour and flavour'}],starterReason:"Cane fruits produce for a decade — the Starter Pack sets up the soil biology and organic matter that improves every single season."},
  rose:{name:'Roses',note:'Demanding flowering shrubs that reward consistent feeding with continuous blooms.',tip:'Apply every 4–6 weeks during the season. Karanja Cake suppresses fungal disease naturally.',essential:[{p:'levelUp',why:'Balanced base for strong canes and foliage'},{p:'flowerPower',why:'High P/K drives continuous blooming all season'},{p:'kelpMeal',why:'Improves disease resistance — critical for black spot and powdery mildew'}],recommended:[{p:'wormCast',why:'Living biology suppresses soil-borne disease'},{p:'karanja',why:'Natural fungicide and fertilizer — suppresses black spot and pests organically'},{p:'boneMeal',why:'Phosphorus for root development and bloom production'}],optional:[{p:'alfalfa',why:'Triacontanol in alfalfa is a proven rose growth stimulant'},{p:'gypsum',why:'Calcium improves petal substance and bloom longevity'},{p:'humicAcid',why:'Improves nutrient uptake for higher bloom frequency'},{p:'insectFrass',why:'Chitosan triggers plant immune defenses against aphids and disease'}],starterReason:"Serious rose growers use the full program. Karanja Cake is also worth adding specifically for rose disease control."},
  sunflower:{name:'Sunflowers',note:'Fast growing annuals that need good nutrition early for stalk, then P/K for head development.',tip:'Work Level Up and Bone Meal into soil at planting. One follow-up top dress at 6 inches with Feather Meal.',essential:[{p:'levelUp',why:'All-purpose feeding for rapid stalk and leaf growth'},{p:'flowerPower',why:'P/K drives the development of large, dense seed heads'},{p:'featherMeal',why:'Slow-release nitrogen feeds the rapid early growth phase'}],recommended:[{p:'boneMeal',why:'Phosphorus for root development and head formation'},{p:'kelpMeal',why:'Micronutrients and stress tolerance for tall exposed plants'},{p:'wormCast',why:'Biology supports fast growth and nutrient turnover'}],optional:[{p:'basalt',why:'Silica for stronger stalks that resist lodging in wind'},{p:'alfalfa',why:'Accelerates early growth for taller stalks'}],starterReason:"For giant sunflowers, the Super Starter Pack is your foundation. Add Feather Meal for maximum height and head size."},
  lavender:{name:'Lavender & Herbs',note:'Herbs prefer lean, well-drained soil. Over-fertilizing reduces essential oils.',tip:'One very light application per season. Focus on minerals and biology rather than high-NPK amendments.',essential:[{p:'kelpMeal',why:'Micronutrients improve essential oil production and fragrance intensity'},{p:'wormCast',why:'Gentle biology without the risk of over-feeding'},{p:'basalt',why:'Slow-release minerals improve flavour and oil concentration'}],recommended:[{p:'levelUp',why:'Light balanced base — use at half the normal rate for herbs'},{p:'azomite',why:'Trace minerals that improve flavour complexity in culinary herbs'}],optional:[{p:'humicAcid',why:'Improves mineral availability in the root zone'},{p:'gypsum',why:'Calcium and sulfur for protein synthesis and flavour compounds'},{p:'dolomite',why:'pH correction if soil is acidic — lavender prefers slightly alkaline'}],starterReason:"Herbs need very little — but if you have a full garden, the Starter Pack covers everything at a fraction of the rate."},
  petunia:{name:'Annuals (Petunias, Marigolds)',note:'Flowering annuals are all about continuous bloom production through the season.',tip:'Work Flower Power and Bone Meal into the soil at planting. One follow-up top dress at 6 weeks.',essential:[{p:'flowerPower',why:'High P/K is the ideal amendment for maximum continuous blooming'},{p:'boneMeal',why:'Slow-release phosphorus for sustained bloom production'},{p:'wormCast',why:'Gentle living nutrition — great for container annuals'}],recommended:[{p:'kelpMeal',why:'Micronutrients and hormones for more flowers and better colour'},{p:'levelUp',why:'Balanced base for establishment — especially in new beds'}],optional:[{p:'alfalfa',why:'Triacontanol boosts bloom frequency in flowering annuals'},{p:'humicAcid',why:'Improves nutrient uptake in container plantings'},{p:'insectFrass',why:'Chitosan reduces aphid and pest pressure on annuals'}],starterReason:"A mixed flower garden benefits from the full Starter Pack — Flower Power and Worm Castings are especially good for containers."},
  perennial:{name:'Perennials',note:'Long-lived plants that benefit from annual soil investment. Build the soil biology once for years of returns.',tip:'Apply once in early spring as growth emerges. Focus on biology and minerals for long-term soil health.',essential:[{p:'levelUp',why:'Balanced annual top dress for vigorous spring growth'},{p:'wormCast',why:'Living biology that improves every season'},{p:'kelpMeal',why:'Stress resistance and micronutrients for winter hardiness'}],recommended:[{p:'flowerPower',why:'P/K for more and bigger blooms on flowering perennials'},{p:'basalt',why:'Slow-release minerals improve vigour year over year'}],optional:[{p:'boneMeal',why:'Phosphorus for root establishment in first year'},{p:'humicAcid',why:'Builds organic matter in the perennial bed over time'},{p:'alfalfa',why:'Triacontanol stimulates vigorous spring emergence'}],starterReason:"Perennials are a long-term investment — the Super Starter Pack builds the soil ecosystem that improves with every passing season."},
  fruit_tree:{name:'Fruit Trees',note:'Trees need large amounts spread across the full drip zone. Apply twice yearly — spring and fall.',tip:'Spread from trunk to drip line in spring. Fall application of Bone Meal and K-Mag builds roots through winter.',essential:[{p:'levelUp',why:'All-purpose balanced nutrition for canopy and root health'},{p:'flowerPower',why:'P/K for fruit set, size, and sweetness'}],recommended:[{p:'boneMeal',why:'Phosphorus for fruit development and root growth'},{p:'kelpMeal',why:'Stress tolerance and disease resistance for long-lived trees'},{p:'kmag',why:'Potassium and magnesium improve fruit quality and sugar content'},{p:'wormCast',why:'Living soil biology under the drip line improves long-term soil health'}],optional:[{p:'basalt',why:'Slow-release rock dust minerals feed trees for years'},{p:'gypsum',why:'Calcium prevents bitter pit in apples and improves fruit firmness'},{p:'humicAcid',why:'Improves deep nutrient availability in the tree root zone'},{p:'fishCompost',why:'Rich organic matter for the large drip zone area'}],starterReason:"Fruit trees are 20–50 year investments. The Starter Pack builds the complete organic foundation — Level Up, Flower Power, Kelp Meal, Worm Castings, and Compost — that feeds the tree for years."},
  ornamental:{name:'Ornamental Shrubs',note:'Low maintenance plants that respond well to one annual spring feeding.',tip:'Work lightly into soil around the drip line each spring. Dolomite Lime if pH needs correction.',essential:[{p:'levelUp',why:'All-purpose annual top dress for healthy growth and colour'},{p:'wormCast',why:'Living biology that improves the soil structure each year'},{p:'kelpMeal',why:'Micronutrients for deep colour and stress tolerance'}],recommended:[{p:'basalt',why:'Broad mineral spectrum for multi-year soil building'},{p:'humicAcid',why:'Improves nutrient availability in established shrub beds'}],optional:[{p:'boneMeal',why:'Phosphorus for flowering shrubs and root establishment'},{p:'dolomite',why:'pH correction for acid-sensitive ornamental shrubs'},{p:'glacialRock',why:'Slow-release minerals for established beds'}],starterReason:"If you have multiple shrubs and garden beds, the Starter Pack gives you the full amendment lineup at the best value price."},
  tropical:{name:'Tropical Houseplants',note:'Indoor plants need much less product. Go light — over-fertilizing is the most common houseplant mistake.',tip:'Use at 25% of outdoor rates. Feed every 6–8 weeks during growing season only. Stop feeding in winter.',essential:[{p:'wormCast',why:'Perfectly gentle — nearly impossible to over-apply. Best amendment for houseplants'},{p:'kelpMeal',why:'Micronutrients and hormones for lush tropical foliage'},{p:'levelUp',why:'Light balanced base — use at a very small pinch per pot'}],recommended:[{p:'humicAcid',why:'Improves nutrient uptake at the very low rates used indoors'},{p:'biochar',why:'Improves moisture and nutrient retention in container soil'}],optional:[{p:'azomite',why:'Trace minerals for vivid foliage colour in tropicals'},{p:'insectFrass',why:'Chitosan provides a level of pest protection indoors'},{p:'yucca',why:'Wetting agent improves water penetration in compacted houseplant soil'}],starterReason:"If you have a large indoor plant collection, the Starter Pack is unbeatable value — each product lasts a very long time at indoor application rates."},
  succulent:{name:'Succulents & Cacti',note:'Minimal feeding is the golden rule. These plants are adapted to poor soils.',tip:'One very small pinch per pot once per year in spring. Focus on drainage and aeration over nutrition.',essential:[{p:'wormCast',why:'Minimal gentle nutrition — the only amendment succulents really need'},{p:'pumice',why:'Improves drainage and aeration — more important than nutrition for succulents'},{p:'basalt',why:'Trace minerals at low rates for healthy compact growth'}],recommended:[{p:'kelpMeal',why:'Micronutrients at very low rates support healthy growth'},{p:'azomite',why:'Trace minerals improve colour and compactness'}],optional:[{p:'humicAcid',why:'Very small amount improves nutrient availability'},{p:'biochar',why:'Improves drainage while retaining the small amount of moisture succulents need'},{p:'glacialRock',why:'Slow-release minerals at very low rates'}],starterReason:"Succulents need almost nothing — but if you have a diverse plant collection, the Starter Pack gives you tools for every plant type."},
  orchid:{name:'Orchids',note:'Highly sensitive epiphytic plants. Minimal feeding and perfect drainage are more important than nutrition.',tip:'Just a pinch of Flower Power around the base when a spike appears. Never apply to dry roots.',essential:[{p:'flowerPower',why:'Tiny amount of P/K during spike formation encourages blooming'},{p:'kelpMeal',why:'Very light application provides hormones that trigger blooming'},{p:'wormCast',why:'The gentlest amendment — a small amount around the bark medium'}],recommended:[{p:'humicAcid',why:'Chelates the small amounts of minerals present in bark media'},{p:'yucca',why:'Wetting agent helps water penetrate the bark medium properly'}],optional:[{p:'azomite',why:'Trace minerals at micro-doses improve bloom colour'},{p:'biochar',why:'Improves moisture retention and air exchange in bark media'}],starterReason:"If you grow orchids alongside other plants, the Starter Pack is the best value way to get Flower Power and Kelp Meal."},
  cannabis_veg:{name:'Cannabis — Vegetative Stage',note:'Veg stage demands nitrogen-rich balanced nutrition for explosive leafy growth and strong root development.',tip:'Mix Level Up and Worm Castings into soil at transplant. Top dress with Alfalfa Meal and Feather Meal at 2–3 weeks.',essential:[{p:'levelUp',why:'Balanced 3-3-3 base — the perfect all-purpose veg amendment'},{p:'featherMeal',why:'Slow-release 11% nitrogen feeds the explosive veg growth phase'},{p:'wormCast',why:'Living soil biology critical for healthy organic veg growth'}],recommended:[{p:'alfalfa',why:'Triacontanol accelerates cell division for faster node stacking'},{p:'kelpMeal',why:'Stress resistance and micronutrients for healthy, compact veg plants'},{p:'insectFrass',why:'Chitosan triggers immune response and adds balanced nutrition'},{p:'humicAcid',why:'Dramatically improves nitrogen uptake efficiency'}],optional:[{p:'crabMeal',why:'Chitin suppresses root pathogens naturally in the veg root zone'},{p:'fishCompost',why:'Rich organic nitrogen and biology for heavy feeding'},{p:'basalt',why:'Silica for stronger stems and internodes'},{p:'maltedBarley',why:'Enzymes break down organic matter faster for accelerated nutrition'}],starterReason:"The Super Starter Pack is the ideal cannabis veg kit — Level Up, Alfalfa Meal, Kelp Meal, Worm Castings, and Compost cover the full veg phase. Add Feather Meal for even more nitrogen."},
  cannabis_flower:{name:'Cannabis — Flowering Stage',note:'Flowering demands high phosphorus and potassium. Switch completely from nitrogen-heavy veg amendments.',tip:'Apply Flower Power, Bone Meal, and K-Mag at flip. Add Kelp Meal at week 3. Stop all feeding 2 weeks before harvest.',essential:[{p:'flowerPower',why:'High P/K — perfectly dialled in for cannabis bloom'},{p:'boneMeal',why:'Slow-release phosphorus for sustained bud development'},{p:'kmag',why:'Potassium and magnesium for bud density and trichome production'}],recommended:[{p:'kelpMeal',why:'Micronutrients and cytokinins improve resin and terpene production'},{p:'wormCast',why:'Living biology continues improving nutrient availability through flower'},{p:'softRockP',why:'Colloidal phosphate for bud swell and density'},{p:'karanja',why:'Suppresses powdery mildew naturally during the vulnerable late flower stage'}],optional:[{p:'gypsum',why:'Sulfur improves terpene production in the final weeks'},{p:'humicAcid',why:'Improves phosphorus uptake during peak flower demand'},{p:'maltedBarley',why:'Enzymes activate the organic amendments faster at the flip'},{p:'insectFrass',why:'Chitosan boosts immune defenses during the flowering window'}],starterReason:"For the full flower program, the Starter Pack is the base — add Bone Meal, K-Mag, and Soft Rock Phosphate for maximum bud density."},
  cannabis_full:{name:'Cannabis — Full Cycle',note:'Full season cannabis needs a complete amendment program. Level Up carries veg; Flower Power takes over at flip.',tip:'Mix veg amendments into soil before transplant. Top dress flower amendments at flip.',essential:[{p:'levelUp',why:'Balanced all-purpose base for the full season'},{p:'flowerPower',why:'P/K bloom booster for the flowering stage'},{p:'wormCast',why:'Living soil biology that feeds the plant through both stages'}],recommended:[{p:'featherMeal',why:'Slow-release nitrogen for the veg phase'},{p:'boneMeal',why:'Phosphorus for flower stage root and bud development'},{p:'kelpMeal',why:'Terpene improvement and stress resistance across both stages'},{p:'kmag',why:'Potassium and magnesium for maximum bud density at harvest'}],optional:[{p:'alfalfa',why:'Triacontanol for faster veg growth and node stacking'},{p:'karanja',why:'Suppresses pests and mildew naturally through the grow'},{p:'humicAcid',why:'Improves nutrient uptake across both stages'},{p:'insectFrass',why:'Chitosan for immune response and added balanced NPK'},{p:'maltedBarley',why:'Enzymes activate amendments faster for quicker uptake'},{p:'softRockP',why:'Colloidal phosphate for bud swell and density in late flower'}],starterReason:"The Super Starter Pack is the perfect full-cycle cannabis kit — Level Up and Alfalfa Meal carry veg, Flower Power covers bloom, and Worm Castings plus Compost keep the living soil thriving all season."},
  lawn:{name:'Lawn / Turf',note:'Lawns need consistent nitrogen and good soil biology. Organic lawn care improves the soil every season.',tip:'Apply Level Up and Compost Blend in early spring and again in fall. Water in thoroughly after application.',essential:[{p:'levelUp',why:'Balanced organic nitrogen that feeds lawns without burning'},{p:'compost',why:'Organic matter improves soil structure and feeds soil biology'},{p:'kelpMeal',why:'Micronutrients for deep green colour and drought tolerance'}],recommended:[{p:'wormCast',why:'Living biology improves soil aeration and thatch breakdown'},{p:'dolomite',why:'pH correction if soil is acidic — lawns prefer pH 6.5–7.0'},{p:'featherMeal',why:'Slow-release nitrogen for sustained green colour'},{p:'humicAcid',why:'Improves nutrient uptake and water retention in turf'}],optional:[{p:'basalt',why:'Slow-release minerals for a more resilient lawn over time'},{p:'zeolite',why:'Improves nutrient and water retention in sandy lawns'},{p:'gypsum',why:'Breaks up clay and improves drainage in compacted lawns'}],starterReason:"If you have a lawn plus garden beds, the Starter Pack covers everything. Level Up and Compost Blend are your lawn workhorses."},
  raised_bed:{name:'Raised Bed (Mixed Veggies)',note:'Raised beds with mixed crops benefit from a complete amendment program — build the soil biology and it keeps improving.',tip:'Work Level Up, Worm Castings, and Compost Blend into the full bed. Apply targeted flower amendments around tomatoes, peppers, and squash only.',essential:[{p:'levelUp',why:'All-purpose base amendment for the full bed'},{p:'wormCast',why:'Living biology that benefits every plant in the bed'},{p:'compost',why:'Rich organic matter foundation for the full bed'}],recommended:[{p:'flowerPower',why:'Apply targeted to fruiting plants only — tomatoes, peppers, squash'},{p:'kelpMeal',why:'Micronutrients and stress tolerance for the full diverse bed'},{p:'boneMeal',why:'Phosphorus for root development across all plant types'},{p:'humicAcid',why:'Improves uptake of all amendments across the full bed'}],optional:[{p:'insectFrass',why:'Pest suppression from chitosan benefits the whole mixed bed'},{p:'basalt',why:'Slow-release minerals improve the bed season over season'},{p:'fishCompost',why:'Additional organic nitrogen and biology for heavy feeders'},{p:'karanja',why:'Natural pest suppression across the whole bed'},{p:'zeolite',why:'Improves water and nutrient retention in raised bed media'}],starterReason:"A mixed raised bed is exactly what the Super Starter Pack is designed for — you get every core amendment to cover all your plants with one order."},
};

// ── State ──
let mode='ground', unit='ft', selectedPot=null, envMode='outdoor';

function buildPotGrid(){
  const g=document.getElementById('pot-grid');
  g.innerHTML=POT_SIZES.map(s=>`<button class="pot-btn" id="pot-${s}" onclick="selectPot(${s})">${s} gal</button>`).join('');
}
buildPotGrid();

function setMode(m){
  mode=m;
  ['btn-ground','btn-pot'].forEach(id=>document.getElementById(id).className='mode-btn');
  document.getElementById('btn-'+m).className='mode-btn active';
  document.getElementById('ground-section').style.display=m==='ground'?'':'none';
  document.getElementById('pot-section').style.display=m==='pot'?'':'none';
  document.getElementById('results').innerHTML='';
  calc();
}

function setUnit(u){
  unit=u;
  document.getElementById('btn-ft').className='unit-btn'+(u==='ft'?' active':'');
  document.getElementById('btn-m').className='unit-btn'+(u==='m'?' active':'');
  calcDims();
}

function setEnv(e){
  envMode=e;
  document.getElementById('env-outdoor').className='env-btn'+(e==='outdoor'?' active':'');
  document.getElementById('env-custom').className='env-btn'+(e==='custom'?' active':'');
  document.getElementById('panel-outdoor').style.display=e==='outdoor'?'':'none';
  document.getElementById('panel-custom').style.display=e==='custom'?'':'none';
  calc();
}

function onPlantChange(){
  const pk=document.getElementById('plant').value;
  const pl=document.getElementById('planner');
  const sub=document.getElementById('planner-sub');
  if(!pk){ pl.style.display='none'; document.getElementById('results').innerHTML=''; return; }
  pl.style.display='';
  if(PLANTS[pk]) sub.textContent=`When to plant, feed &amp; harvest — ${PLANTS[pk].name}`;
  calc();
}

function calcDims(){
  const l=parseFloat(document.getElementById('dim-length').value)||0;
  const w=parseFloat(document.getElementById('dim-width').value)||0;
  const dft=parseFloat(document.getElementById('dim-depth-ft').value)||0;
  const din=parseFloat(document.getElementById('dim-depth-in').value)||0;
  const depthIn = dft*12 + din; // total depth in inches
  const disp=document.getElementById('area-display');
  if(l>0&&w>0){
    disp.style.display='block';
    const depthLabel = depthIn>0 ? ` × ${dft>0?dft+'ft ':''} ${din>0?din+'"':''} deep` : '';
    if(unit==='ft'){
      const sqft=l*w;
      const cuft=(sqft*depthIn/12).toFixed(1);
      document.getElementById('area-text').innerHTML=
        `${l} ft × ${w} ft = <strong>${sqft.toLocaleString()} sq ft</strong>` +
        (depthIn>0 ? `<br>${depthIn}" deep · <strong>${cuft} cu ft</strong> of soil` : '<br>No depth entered — using standard 6" amendment rate');
    } else {
      const sqm=l*w;
      const cum=(sqm*(depthIn/12)*0.0283168).toFixed(2);
      document.getElementById('area-text').innerHTML=
        `${l} m × ${w} m = <strong>${sqm.toLocaleString()} m²</strong>` +
        (depthIn>0 ? `<br>${depthIn}" deep · <strong>${cum} m³</strong> of soil` : '<br>No depth entered — using standard 6" amendment rate');
    }
  } else disp.style.display='none';
  calc();
}

function selectPot(s){
  selectedPot=s;
  document.getElementById('custom-gal').value='';
  POT_SIZES.forEach(p=>{const b=document.getElementById('pot-'+p);if(b)b.className='pot-btn'+(p===s?' active':'');});
  calc();
}
function setCustomPot(){
  selectedPot=null;
  POT_SIZES.forEach(p=>{const b=document.getElementById('pot-'+p);if(b)b.className='pot-btn';});
  calc();
}

function lbsToGrams(lb){return lb*453.592;}
function tbspToLbs(t){return t*0.0375;}
function lbs100ToTbsp100(l){return l/0.0375;}
function fT(t){if(t<0.1)return '<0.1';if(t<10)return t.toFixed(1);return Math.round(t).toLocaleString();}
function fL(l){if(l<0.01)return '<0.1';if(l<0.1)return l.toFixed(2);return l.toFixed(1);}

function makeCard(pk,why,gal,sqft,np,dm){
  dm=dm||1; // depth multiplier (1 = standard 6" depth)
  const p=PRODUCTS[pk]; if(!p)return '';

  const bs=p.bagSize||5;
  const vol=(pk==='wormCast'||pk==='compost'); // sold by volume (1 L, 1 gallon), not weight
  if(gal){
    const tpp=p.tbsp*gal,lpp=tbspToLbs(tpp),tl=lpp*(np||1),ttbsp=tpp*(np||1),tg=Math.round(lbsToGrams(tl)),bags=Math.ceil(tl/bs);
    if(vol){const gl=Math.ceil(ttbsp/256),lit=ttbsp/67.63;
      return `<div class="product-card"><div class="product-top"><span class="product-name"><a href="${p.url}" target="_blank" style="color:#1a4a2e;text-decoration:none">${p.name}</a></span><span style="font-size:11px;color:#888;font-weight:600">${p.npk}</span></div><div class="product-npk">${why}</div><div class="amounts amounts-pot"><div class="amount-box hi"><div class="amount-num">${fT(tpp)}</div><div class="amount-lbl">tbsp / pot<br><span style="font-size:9px;color:#999">mix into top inch</span></div></div><div class="amount-box"><div class="amount-num">${fL(lit)} L</div><div class="amount-lbl">${np>1?'litres total ('+np+' pots)':'litres per pot'}</div></div><div class="amount-box"><div class="amount-num">${gl}</div><div class="amount-lbl">gallon bag${gl!==1?'s':''}<br><span style="font-size:9px;color:#999">sold by volume</span></div></div></div></div>`;}
    return `<div class="product-card"><div class="product-top"><span class="product-name"><a href="${p.url}" target="_blank" style="color:#1a4a2e;text-decoration:none">${p.name}</a></span><span style="font-size:11px;color:#888;font-weight:600">${p.npk}</span></div><div class="product-npk">${why}</div><div class="amounts amounts-pot"><div class="amount-box hi"><div class="amount-num">${fT(tpp)}</div><div class="amount-lbl">tbsp / pot<br><span style="font-size:9px;color:#999">mix into top inch</span></div></div><div class="amount-box"><div class="amount-num">${np>1?fT(ttbsp)+' tbsp':fL(lpp)+' lbs'}</div><div class="amount-lbl">${np>1?'tbsp total ('+np+' pots)':'lbs per pot'}</div></div><div class="amount-box"><div class="amount-num">${bags}</div><div class="amount-lbl">bag${bags!==1?'s':''} (${bs} lb)<br><span style="font-size:9px;color:#999">${tg}g total</span></div></div></div></div>`;
  } else {
    const lt=sqft*p.lbs100/100*dm,tt=sqft*lbs100ToTbsp100(p.lbs100)/100*dm,t10=10*lbs100ToTbsp100(p.lbs100)/100*dm,tg=Math.round(lbsToGrams(lt)),bags=Math.ceil(lt/bs);
    if(vol){const gl=Math.ceil(tt/256),lit=tt/67.63;
      return `<div class="product-card"><div class="product-top"><span class="product-name"><a href="${p.url}" target="_blank" style="color:#1a4a2e;text-decoration:none">${p.name}</a></span><span style="font-size:11px;color:#888;font-weight:600">${p.npk}</span></div><div class="product-npk">${why}</div><div class="amounts amounts-ground"><div class="amount-box hi"><div class="amount-num">${fT(tt)}</div><div class="amount-lbl">tbsp total<br><span style="font-size:9px;color:#999">whole bed</span></div></div><div class="amount-box"><div class="amount-num">${fT(t10)}</div><div class="amount-lbl">tbsp per<br>10 sq ft</div></div><div class="amount-box"><div class="amount-num">${fL(lit)} L</div><div class="amount-lbl">litres total<br><span style="font-size:9px;color:#999">whole bed</span></div></div><div class="amount-box"><div class="amount-num">${gl}</div><div class="amount-lbl">gallon bag${gl!==1?'s':''}<br><span style="font-size:9px;color:#999">sold by volume</span></div></div></div></div>`;}
    return `<div class="product-card"><div class="product-top"><span class="product-name"><a href="${p.url}" target="_blank" style="color:#1a4a2e;text-decoration:none">${p.name}</a></span><span style="font-size:11px;color:#888;font-weight:600">${p.npk}</span></div><div class="product-npk">${why}</div><div class="amounts amounts-ground"><div class="amount-box hi"><div class="amount-num">${fT(tt)}</div><div class="amount-lbl">tbsp total<br><span style="font-size:9px;color:#999">whole bed</span></div></div><div class="amount-box"><div class="amount-num">${fT(t10)}</div><div class="amount-lbl">tbsp per<br>10 sq ft</div></div><div class="amount-box"><div class="amount-num">${fL(lt)}</div><div class="amount-lbl">lbs total<br><span style="font-size:9px;color:#999">${tg}g</span></div></div><div class="amount-box"><div class="amount-num">${bags}</div><div class="amount-lbl">bag${bags!==1?'s':''} (${bs} lb)</div></div></div></div>`;
  }
}

function calc(){
  const pk=document.getElementById('plant').value;
  const el=document.getElementById('results');
  if(!pk){el.innerHTML='';return;}
  const plant=PLANTS[pk];

  let sqft=0,gal=null,np=1,sizeLabel='',depthMult=1;
  if(mode==='ground'){
    const l=parseFloat(document.getElementById('dim-length').value)||0;
    const w=parseFloat(document.getElementById('dim-width').value)||0;
    if(!l||!w){el.innerHTML='';return;}
    const dft=parseFloat(document.getElementById('dim-depth-ft').value)||0;
    const din=parseFloat(document.getElementById('dim-depth-in').value)||0;
    const depthIn = dft*12+din || 6; // default 6 inches if not set
    const depthMult = depthIn/6; // 6" = 1x baseline
    if(unit==='ft'){sqft=l*w;sizeLabel=`${l} ft × ${w} ft, ${depthIn}" deep (${sqft.toLocaleString()} sq ft)`;}
    else{const sqm=l*w;sqft=sqm/0.0929;sizeLabel=`${l} m × ${w} m, ${depthIn}" deep (${sqm.toLocaleString()} m²)`;}
  } else {
    const cg=parseFloat(document.getElementById('custom-gal').value);
    gal=selectedPot||(cg>0?cg:null);
    np=parseInt(document.getElementById('num-pots').value)||1;
    if(!gal){el.innerHTML='';return;}
    sizeLabel=np===1?`${gal} gal pot`:`${np} × ${gal} gal pots`;
    depthMult=1; // pots don't use depth multiplier
  }

  // Cycle planner
  const zoneKey = envMode==='outdoor' ? (document.getElementById('zone-select').value||'') : '';
  const cv = envMode==='custom' ? document.getElementById('cust-veg').value : '';
  const cf = envMode==='custom' ? document.getElementById('cust-flower').value : '';
  const cycle = buildCycleInfo(pk, zoneKey, cv, cf);

  // Update zone result panel
  const zrEl = document.getElementById('zone-result');
  const crEl = document.getElementById('custom-result');
  if(zrEl){
    if(envMode==='outdoor' && (zoneKey || cycle)){
      zrEl.innerHTML = zoneKey ? renderCycleBlock(cycle) : '';
    } else { zrEl.innerHTML=''; }
  }
  if(crEl){
    if(envMode==='custom' && cycle){
      crEl.innerHTML = renderCycleBlock(cycle);
    } else if(crEl){ crEl.innerHTML=''; }
  }

  // Cycle banner in results
  let cycleBanner='';
  if(cycle && cycle.lines && cycle.lines.length && zoneKey){
    cycleBanner=`<div class="cycle-banner"><strong>📅 Your growing cycle — ${cycle.zoneLabel}:</strong><br>${cycle.lines.join('<br>')}</div>`;
  }

  const starters=['Level Up 3-3-3','Flower Power 2-6-4','Kelp Meal 1-0-4','Alfalfa Meal 3-0.5-3','Worm Castings','Compost Blend'];

  el.innerHTML=`<div class="results">
    <div class="results-header"><h2>${plant.name}</h2><p>${sizeLabel} — scroll down for all recommendations</p></div>
    <div class="plant-info">${plant.note}</div>
    ${cycleBanner}
    <div class="tier-header tier-essential">Essential — start here</div>
    ${plant.essential.map(e=>makeCard(e.p,e.why,gal,sqft,np,depthMult)).join('')}
    <div class="tier-header tier-recommended">Recommended — level up your results</div>
    ${plant.recommended.map(e=>makeCard(e.p,e.why,gal,sqft,np,depthMult)).join('')}
    <div class="tier-header tier-optional">Optional — for serious growers</div>
    ${plant.optional.map(e=>makeCard(e.p,e.why,gal,sqft,np,depthMult)).join('')}
    <div class="tip"><strong>Pro tip:</strong> ${plant.tip} All Mario's products are 100% organic and Canadian-made. Any extra stores well for your next top dress.</div>
    <div class="upgrade-card">
      <div class="upgrade-top">
        <div class="upgrade-left"><h3>Super Starter Pack — the complete kit</h3><p>Get the 5 most essential amendments in one bundle at the best value price.</p></div>
        <span class="upgrade-badge">Best Value</span>
      </div>
      <div class="upgrade-reason">${plant.starterReason}</div>
      <div class="upgrade-includes">
        ${starters.map(n=>`<div class="upgrade-item"><div class="upgrade-dot"></div>${n}</div>`).join('')}
        <div class="upgrade-item"><div class="upgrade-dot"></div>Best value bundle</div>
      </div>
      <a class="upgrade-cta" href="https://mariossupersoil.ca/super-starter-pack" target="_blank">Shop the Super Starter Pack</a>
    </div>
  </div>`;
}
