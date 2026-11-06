<div class="mode-toggle">
    <button class="mode-btn active" id="btn-ground" onclick="setMode('ground')">Garden / Raised Bed</button>
    <button class="mode-btn" id="btn-pot" onclick="setMode('pot')">Container / Pot</button>
  </div>

  <div class="section">
    <div class="label">What are you growing?</div>
    <select id="plant" onchange="onPlantChange()">
      <option value="">— select a plant —</option>
      <optgroup label="Vegetables">
        <option value="tomato">Tomatoes</option>
        <option value="pepper">Peppers &amp; Chili</option>
        <option value="cucumber">Cucumbers &amp; Zucchini</option>
        <option value="lettuce">Lettuce &amp; Greens</option>
        <option value="carrot">Root Vegetables (Carrots, Beets)</option>
        <option value="squash">Squash &amp; Pumpkins</option>
        <option value="bean">Beans &amp; Peas</option>
        <option value="corn">Corn</option>
        <option value="brassica">Brassicas (Kale, Broccoli, Cabbage)</option>
        <option value="garlic">Garlic &amp; Onions</option>
      </optgroup>
      <optgroup label="Fruits &amp; Berries">
        <option value="strawberry">Strawberries</option>
        <option value="blueberry">Blueberries</option>
        <option value="raspberry">Raspberries &amp; Blackberries</option>
      </optgroup>
      <optgroup label="Flowers">
        <option value="rose">Roses</option>
        <option value="sunflower">Sunflowers</option>
        <option value="lavender">Lavender &amp; Herbs</option>
        <option value="petunia">Annuals (Petunias, Marigolds)</option>
        <option value="perennial">Perennials</option>
      </optgroup>
      <optgroup label="Trees &amp; Shrubs">
        <option value="fruit_tree">Fruit Trees</option>
        <option value="ornamental">Ornamental Shrubs</option>
      </optgroup>
      <optgroup label="Indoor / Houseplants">
        <option value="tropical">Tropical Houseplants</option>
        <option value="succulent">Succulents &amp; Cacti</option>
        <option value="orchid">Orchids</option>
      </optgroup>
      <optgroup label="Cannabis">
        <option value="cannabis_veg">Cannabis — Vegetative Stage</option>
        <option value="cannabis_flower">Cannabis — Flowering Stage</option>
        <option value="cannabis_full">Cannabis — Full Cycle</option>
      </optgroup>
      <optgroup label="Lawn &amp; General">
        <option value="lawn">Lawn / Turf</option>
        <option value="raised_bed">Raised Bed (Mixed Veggies)</option>
      </optgroup>
    </select>
  </div>

  <div id="ground-section" class="section">
    <div class="label">Garden size — length × width</div>
    <div class="dim-row">
      <div><div class="label" style="margin-bottom:4px">Length</div><input type="number" id="dim-length" placeholder="e.g. 10" min="1" oninput="calcDims()"/></div>
      <div class="dim-x">×</div>
      <div><div class="label" style="margin-bottom:4px">Width</div><input type="number" id="dim-width" placeholder="e.g. 10" min="1" oninput="calcDims()"/></div>
    </div>
    <div class="unit-btns">
      <button class="unit-btn active" id="btn-ft" onclick="setUnit('ft')">feet</button>
      <button class="unit-btn" id="btn-m" onclick="setUnit('m')">metres</button>
    </div>
    <div class="depth-row">
      <div>
        <div class="label" style="margin-bottom:4px">Soil depth (feet)</div>
        <input type="number" id="dim-depth-ft" placeholder="e.g. 1" min="0" value="0" oninput="calcDims()"/>
      </div>
      <div>
        <div class="label" style="margin-bottom:4px">Soil depth (inches)</div>
        <input type="number" id="dim-depth-in" placeholder="e.g. 6" min="0" max="11" value="6" oninput="calcDims()"/>
      </div>
      <div style="padding-bottom:2px;font-size:12px;color:#888;white-space:nowrap;align-self:center">↕ depth</div>
    </div>
    <p class="depth-note">Depth is how deep you're amending the soil — typically 6" for top dress / top dress, 12" for a new raised bed being filled from scratch.</p>
    <div id="area-display" class="area-display" style="display:none;margin-top:8px"><span id="area-text"></span></div>
  </div>

  <div id="pot-section" class="section" style="display:none">
    <div class="label">Pot size</div>
    <div class="pot-grid" id="pot-grid"></div>
    <div class="pot-num-row">
      <div><div class="label">or enter size (gal)</div><input type="number" id="custom-gal" placeholder="e.g. 15" min="0.5" step="0.5" oninput="setCustomPot()"/></div>
      <div><div class="label">number of pots</div><input type="number" id="num-pots" placeholder="e.g. 4" min="1" value="1" oninput="calc()"/></div>
    </div>
  </div>

  <!-- GROWING SEASON PLANNER -->
  <div class="planner" id="planner" style="display:none">
    <div class="planner-head">
      <span style="font-size:22px">📅</span>
      <div class="planner-head-text">
        <h3>Growing Season Planner</h3>
        <p id="planner-sub">Select your region to get a recommended planting &amp; feeding schedule</p>
      </div>
    </div>
    <div class="planner-body">
      <div class="env-toggle">
        <button class="env-btn active" id="env-outdoor" onclick="setEnv('outdoor')">🌤 Outdoor / I'm not sure</button>
        <button class="env-btn" id="env-custom" onclick="setEnv('custom')">⚙️ Custom (I know my schedule)</button>
      </div>

      <div id="panel-outdoor">
        <div class="label" style="margin-top:.1rem">Your region</div>
        <select id="zone-select" onchange="calc()">
          <option value="">— choose your province, state, or zone —</option>
          <optgroup label="🍁 Canada">
            <option value="bc_coast">BC — Coastal (Vancouver, Victoria, Nanaimo) · Zone 8</option>
            <option value="bc_int">BC — Interior (Kelowna, Kamloops, Prince George) · Zone 4–6</option>
            <option value="ab">Alberta (Calgary, Edmonton, Red Deer) · Zone 3–4</option>
            <option value="sk">Saskatchewan (Saskatoon, Regina) · Zone 2–3</option>
            <option value="mb">Manitoba (Winnipeg, Brandon) · Zone 2–3</option>
            <option value="on_sw">Ontario — SW (Windsor, London, Hamilton) · Zone 6–7</option>
            <option value="on_gta">Ontario — GTA / Niagara / St. Catharines / Kingston · Zone 5–6</option>
            <option value="on_ne">Ontario — North/East (Ottawa, Sudbury) · Zone 4–5</option>
            <option value="on_fn">Ontario — Far North (Thunder Bay, Timmins) · Zone 2–3</option>
            <option value="qc_s">Québec — South (Montréal, Québec City, Sherbrooke) · Zone 4–5</option>
            <option value="qc_n">Québec — North (Saguenay, Rimouski) · Zone 2–3</option>
            <option value="ns_nb">Nova Scotia / New Brunswick · Zone 5–6</option>
            <option value="pei">Prince Edward Island · Zone 6</option>
            <option value="nl">Newfoundland &amp; Labrador · Zone 4–5</option>
          </optgroup>
          <optgroup label="🇺🇸 USA — Northern (Zone 3–5)">
            <option value="us3">Zone 3 — Northern MN, ND, MT highlands</option>
            <option value="us4">Zone 4 — Minnesota, Wisconsin, upstate NY, Vermont, Maine</option>
            <option value="us5">Zone 5 — Michigan, Illinois, Ohio, Pennsylvania, Massachusetts</option>
          </optgroup>
          <optgroup label="🇺🇸 USA — Mid (Zone 6–7)">
            <option value="us6">Zone 6 — Virginia, Missouri, New Jersey, Indiana, Colorado</option>
            <option value="us7">Zone 7 — Tennessee, North Carolina, Oregon coast, WA coast</option>
          </optgroup>
          <optgroup label="🇺🇸 USA — Southern / Pacific (Zone 8+)">
            <option value="us8">Zone 8 — Georgia, Texas, Pacific NW lowlands, northern CA</option>
            <option value="us9">Zone 9+ — Southern CA, Florida, Gulf Coast, Arizona lowlands</option>
          </optgroup>
        </select>
        <div id="zone-result"></div>
      </div>

      <div id="panel-custom" style="display:none">
        <div class="label" style="margin-top:.1rem">Enter your exact schedule (weeks)</div>
        <div class="custom-grid">
          <div>
            <div class="label" style="margin-bottom:4px;color:#2d7a4a">🌱 Veg / Establish weeks</div>
            <input type="number" id="cust-veg" placeholder="e.g. 8" min="1" max="52" oninput="calc()"/>
          </div>
          <div>
            <div class="label" style="margin-bottom:4px;color:#d35400">🌸 Flower / Fruit weeks</div>
            <input type="number" id="cust-flower" placeholder="e.g. 9" min="1" max="52" oninput="calc()"/>
          </div>
        </div>
        <p class="custom-note">For cannabis: veg = weeks under 18+ hr light; flower = 12/12 until harvest. For outdoor veggies: veg = weeks from transplant to first flower; fruit = weeks until harvest. Leave blank to use defaults.</p>
        <div id="custom-result"></div>
      </div>
    </div>
  </div>

  <div id="results"></div>
