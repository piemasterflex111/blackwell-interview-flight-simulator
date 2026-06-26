# Interview Practice Plan — All Stories Mapped

**How to use:** Practice each story in order. For each one:
1. Read the 10/10 answer aloud
2. Run the simulator on that topic
3. Record your actual answer
4. Note where you drifted from the 10/10 version

---

## PHASE 1 — Terran Orbital (Highest Priority)

These are the bullets they will drill hardest. Practice these first and deepest.

### Story 1: 16-Channel Test Station Architecture

**Resume bullet:** "Designed and implemented a 16-channel RS-422 flashing and telemetry station for spacecraft battery module validation, expanding parallel test capacity from 8 to 16 channels. Defined station architecture across power distribution (66 V), enable lines (3.3 V), RS-422 communication paths, COM-port mapping, physical integration, and operator workflow."

**What you actually did:** Designed the physical station concept (enclosure, harness, connectors, channel layout). EGSE fabricated it from your technical package. You owned bring-up, validation, mapping, and debug. Did NOT write the LabVIEW test software or pyserial code.

**10/10 answer:**
"I designed the station architecture that our EGSE team fabricated. It was a Protocase enclosure, 16-lane RS-422, 66 V power bus, and 3.3 V enable lines. I defined the connector placement, channel layout, and harness package they built from. After fabrication, I owned bring-up — mapping which COM ports connected to which modules, validating signal integrity, and confirming the test workflow matched the module requirements. The station validated at lower channel counts with good throughput, and we identified practical scaling limits at higher parallel counts."

**Likely follow-ups:**
- How did you decide the channel layout?
- What were the scaling limits you hit?
- How did COM-port mapping work?

---

### Story 2: Fixture Commissioning and Debug (Golden-Unit Methodology)

**Resume bullet:** "Validated harness continuity, connector pinouts, power sequencing, and communication paths. Used golden-unit methodology (proven-good DUT, known-good ports, controlled swaps) to isolate failures across DUT, harness, station, firmware, and operator layers."

**What you actually did:** Physically validated the built station — continuity checks on harness, pinout verification, power sequencing confirmation. Used proven-good battery modules as reference DUTs to swap and isolate where failures lived.

**10/10 answer:**
"Once the station was built, I did the full commissioning pass. Started with physical checks — harness continuity with a DMM, connector pinouts against the schematic, power sequencing on the 66 V bus. Then moved to commissioning with a golden unit: a battery module we knew was good. If the golden unit failed on a port, the problem was in the station, not the DUT. If it passed there but failed elsewhere, the problem was in the harness or connector. I systematically isolated failures down to the specific layer — DUT, harness, station, or firmware — so we could fix the right thing."

**Likely follow-ups:**
- Walk me through a time golden-unit methodology found a hardware issue
- How did you decide which layer was failing?

---

### Story 3: Communication Troubleshooting

**Resume bullet:** "Diagnosed RS-422 communication failures including RX/TX reversal, shorts, intermittent drops, COM-port enumeration conflicts, and signal integrity issues using oscilloscope measurements, continuity checks, and serial telemetry analysis."

**What you actually did:** Debugged RS-422 communication failures on the station. Found wiring issues, signal problems, COM-port conflicts. Used oscilloscope and continuity checks as physical verification.

**10/10 answer:**
"I've debugged RS-422 failures at multiple levels. The most common: RX/TX pin reversal in the harness — showed up as module not responding, looked like a firmware issue until you checked pinouts. Then shorts on the differential pair — dropped signal integrity, intermittent communication. And COM-port enumeration conflicts when Windows renumbered ports between sessions. I'd start with continuity checks on the harness, move to oscilloscope measurements on the RS-422 differential pair to check signal integrity, and verify the COM-port mapping matched the module layout. The key was knowing which layer to check first — physical wiring before blaming firmware."

**Likely follow-ups:**
- What's RS-422 differential signaling?
- What voltage levels did you see on the scope?
- How did you handle COM-port enumeration conflicts?

---

### Story 4: Python Validation Automation

**Resume bullet:** "Built Python RS-232 serial logging scripts to capture weld telemetry from virtual COM ports, converting manual observation into structured CSV records for validation review."

**What you actually did:** Python serial logging only. Captured weld telemetry from virtual COM ports, output to CSV. This is a separate project from the 16-lane station — different context, different equipment.

**10/10 answer:**
"For weld validation, the process was manual — an operator watched a screen and took notes. I built a Python script using the pyserial library that connected to the virtual COM port, captured the telemetry stream, and logged it to a structured CSV with timestamps. That way, every weld had a data record we could review later instead of relying on handwritten notes. It was straightforward serial I/O — open the COM port, read the stream, parse the fields, write to CSV — but it replaced a manual step and made the validation record traceable."

**Likely follow-ups:**
- What library did you use?
- How did you handle COM-port disconnections?
- How did you parse the telemetry stream?

---

### Story 5: Production Line Leadership

**Resume bullet:** "Led spacecraft battery module line restart including process control updates, weld schedule requalification, and cross-functional coordination. Documented salvage/rework procedures for 250+ units while preserving traceability across process, hardware, and test records."

**What you actually did:** When the production line was restarted, you updated the process controls and requalified the weld schedule. Handled 250+ units that needed salvage or rework, documented procedures so traceability was preserved.

**10/10 answer:**
"When we restarted the production line, the weld schedule needed requalification against the current process controls. I led the restart — updated the control plan, coordinated with welding techs on the requalification steps, and documented the rework procedures for units that had been in process during the shutdown. Over 250 units needed salvage or rework, and each one had to maintain traceability — so I documented which process step each unit was at, what rework was applied, and what test results came out. The goal was to restart the line without losing quality records for any unit."

**Likely follow-ups:**
- What was the shutdown about?
- How did you track 250+ units individually?
- What process controls did you update?

---

### Story 6: Cross-Functional Issue Resolution

**Resume bullet:** "Served as liaison between manufacturing, test, quality, and design engineering to document observed vs. expected behavior and drive corrective actions. Explained production blockers, aligned corrective actions, and restored execution flow for complex aerospace test workflows."

**What you actually did:** You were the bridge between manufacturing, test, quality, and design engineering. Documented what was happening vs what should happen, drove corrective actions to fix production blockers.

**10/10 answer:**
"I was the point of contact when test or production hit a blocker that crossed department lines. My job was to document what was actually happening versus what the spec said should happen, then coordinate with the right team to fix it. If a batch of modules failed communication on the test station, I'd verify whether it was a station issue, a DUT issue, or a firmware issue — then route it to the right team with evidence. The corrective action wasn't just 'fix it' — it was documenting what was found, what was changed, and confirming the fix held on the next batch. That kept the line moving and kept quality records clean."

**Likely follow-ups:**
- Give me an example of a cross-functional issue you resolved
- How did you handle disagreement between teams?
- What was your escalation path?

---

## PHASE 2 — Mercury Systems

Medium priority. Expect 1-2 questions from this role.

### Story 7: Environmental Qualification Testing

**Resume bullet:** "Executed MIL-STD-810 environmental qualification test protocols including temperature cycling, shock, vibration, and static exposure. Monitored test execution, captured measurement data, and tracked deviations."

**What you actually did:** Ran environmental qualification tests on defense electronics per MIL-STD-810. Temperature cycling, shock, vibration, static exposure. Monitored the tests, captured measurement data, tracked deviations from spec.

**10/10 answer:**
"I ran MIL-STD-810 qualification tests on defense electronics — temperature cycling, shock, vibration, and static exposure. Each test had a specific profile: temperature cycling was typically -40 to +71 C over multiple cycles, shock was specific pulse durations and G-levels, vibration followed defined sweep profiles. My job was to set up the unit in the test chamber, run the profile, capture the measurement data throughout, and track any deviations from the spec. If the unit failed at a certain temperature or vibration level, that went into the failure log with the exact test condition documented."

**Likely follow-ups:**
- What was the most common failure mode?
- How did you handle a deviation during a test?
- What did the test chamber setup look like?

---

### Story 8: Test Instrumentation

**Resume bullet:** "Operated and maintained environmental test chambers, data acquisition systems, power supplies, DMM, oscilloscope, and control electronics supporting qualification tests."

**What you actually did:** Operated and maintained the test equipment used for qualification testing. Chambers, DA systems, power supplies, oscilloscopes, DMMs.

**10/10 answer:**
"I operated the environmental test chambers — setting up temperature cycling profiles, loading the DUT with proper thermal coupling, and monitoring the chamber controls throughout the test. For data acquisition, I set up DA systems to capture temperature, voltage, and current measurements at defined intervals. I also maintained the bench equipment — power supplies, DMMs, oscilloscopes — making sure they were calibrated and the measurement setups were repeatable across test runs. The goal was consistent data across multiple qualification cycles."

**Likely follow-ups:**
- What DA system did you use?
- How did you verify calibration?
- What sample rate did you use for measurements?

---

### Story 9: Failure Analysis

**Resume bullet:** "Contributed to structured root-cause tracking and corrective-action workflows for qualification test anomalies. Isolated failures to specific stress conditions and documented corrective action steps for engineering review."

**What you actually did:** Contributed to root-cause tracking when qualification tests showed anomalies. Isolated failures to the specific stress condition that caused them. Documented corrective actions for engineering review.

**10/10 answer:**
"When a unit failed a qualification test, the process was to isolate exactly what stress caused it. If it failed during temperature cycling, was it the low temp, the high temp, or the transition? Did it survive the same profile the next time? I'd document the failure condition, the measurement data around the failure, and any visual inspection findings. Then we'd work with design engineering on whether it was a unit-specific issue, a process issue, or a design margin issue. The corrective action steps were documented so they could be reviewed and tracked to closure."

**Likely follow-ups:**
- Give me an example of a root cause you found
- How did you separate unit-specific from systemic failures?

---

### Story 10: Validation Evidence Packages

**Resume bullet:** "Built structured qualification evidence packages with measurement data, configuration history, failure logs, corrective actions, and retest results for engineering review and audit."

**What you actually did:** Compiled qualification evidence packages with measurement data, config history, failure logs, corrective actions, and retest results. These were used for engineering review and audit.

**10/10 answer:**
"Every qualification test needed a complete evidence package. That meant pulling the measurement data from the DA system, documenting the test configuration and setup, any failures that occurred with the specific conditions, corrective actions taken, and retest results if there was a failure and requalification. The package had to be auditable — someone else should be able to review it and confirm the unit was tested to spec, failures were documented and resolved, and the retest passed. I structured these so they could be submitted for engineering review without needing me to explain what was in them."

**Likely follow-ups:**
- How did you organize the evidence packages?
- What was the review process?

---

## PHASE 3 — Gatekeeper Systems / Channel Vision

Lower priority. These show embedded systems exposure and early Python work.

### Story 11: Firmware Validation

**Resume bullet:** "Validated firmware and configuration updates by confirming boot state, reported version, device communication, persistence after power cycle, and observable physical device behavior."

**What you actually did:** Validated firmware updates on embedded devices. Confirmed boot state, version, communication, power cycle persistence, and physical behavior.

**10/10 answer:**
"Firmware validation meant confirming the update actually took. I'd flash the firmware, then verify: boot state — did it come up clean? Version — did it report the right build number? Communication — could it talk on the expected protocol? Power cycle — did it persist after a hard reset? Physical behavior — did the device actually do what it was supposed to do? All five checks had to pass before the firmware was marked validated. If any one failed, we'd document which one and work backward to figure out where the flash process broke."

**Likely follow-ups:**
- What happened if power cycle failed?
- How did you verify version numbers?

---

### Story 12: Python-Assisted Testing

**Resume bullet:** "Built Python UART and I2C workflow scripts for sensor data capture, per-unit validation records, and firmware flash verification. Converted manual validation steps into repeatable scripted workflows."

**What you actually did:** Built Python scripts for UART and I2C communication. Captured sensor data, created per-unit validation records, verified firmware flashes. Converted manual steps into scripts.

**10/10 answer:**
"Manual validation meant an operator sitting at a terminal, typing commands, and recording results. I scripted the UART and I2C communication in Python so the same sequence ran every time. The script would connect via UART, send the verification commands, capture the responses, and write a per-unit validation record. For sensor testing over I2C, it would read the sensor registers, compare against expected values, and log pass/fail. The key benefit was consistency — the same steps, same timing, same results every time, regardless of which operator ran it."

**Likely follow-ups:**
- What was the sensor I2C setup?
- How did you handle script errors mid-run?

---

### Story 13: Embedded Debugging

**Resume bullet:** "Used JTAG-assisted workflows for board bring-up, firmware flashing, and hardware troubleshooting. Developed structured troubleshooting procedures for field issue investigation."

**What you actually did:** Used JTAG for board bring-up and firmware flashing. Created troubleshooting procedures for field issues.

**10/10 answer:**
"JTAG was our recovery path when the normal boot process failed. If a board wouldn't boot from the flashed firmware, we'd connect the JTAG debugger, verify the hardware was alive, and flash from the debugger. For board bring-up, JTAG let us verify the CPU was running, memory was responding, and the boot sequence was executing — before the main firmware even loaded. I documented the troubleshooting steps so field techs could follow them: check power, check boot mode pins, connect JTAG, verify hardware, then attempt firmware recovery."

**Likely follow-ups:**
- What JTAG debugger did you use?
- What did 'hardware alive' mean in practice?

---

### Story 14: Documentation

**Resume bullet:** "Created technical documentation for validation procedures, firmware update processes, and customer-facing issue follow-up."

**What you actually did:** Wrote validation procedures, firmware update processes, and customer issue follow-up documentation.

**10/10 answer:**
"The documentation had to serve two audiences: technicians who needed step-by-step procedures, and customers who needed to understand what was tested and what the results were. For validation procedures, that meant clear steps with expected results at each stage — if step 3 says 'verify boot state,' the operator should know exactly what 'pass' looks like. For customer follow-up, it was more about documenting what issue was reported, what investigation was done, and what resolution was reached. The goal was clarity — someone shouldn't have to call me to understand what was done."

**Likely follow-ups:**
- How did you structure the procedures?
- What format did you use?

---

## PHASE 4 — Personal Projects

Lower priority. These show initiative and technical depth in Python.

### Story 15: Python Validation & Automation Framework

**Resume bullet:** "Built a FastAPI service-layer architecture for structured data workflows, implementing SQLAlchemy data models, service-layer boundaries, and pytest integration testing."

**What you actually did:** Built a FastAPI + SQLAlchemy + pytest project to learn backend architecture. Implemented service-layer patterns, data models, and integration tests. This is a learning project, not production code.

**10/10 answer:**
"I built a FastAPI project to learn backend architecture — specifically the service-layer pattern. I set up SQLAlchemy models for data storage, separated the service layer from the API layer so business logic could be tested independently, and wrote pytest integration tests that verified the full request-to-database flow. It was a learning project — not production code — but it gave me hands-on experience with the patterns I see in job descriptions: ORM usage, service boundaries, and test coverage on the data layer."

**Likely follow-ups:**
- Why service-layer pattern?
- What testing approach did you use?
- How would you scale this for production?

---

### Story 16: Jira/GitHub Workflow Automation Pipeline

**Resume bullet:** "Built data pipelines that pull Jira and GitHub REST API data, flatten nested JSON payloads, compute metrics, and generate Markdown/HTML reports."

**What you actually did:** Built scripts that pull data from Jira and GitHub REST APIs, flatten nested JSON, compute metrics, and generate reports. Separated API fetching from transformation logic for testability.

**10/10 answer:**
"I built automation pipelines that pull data from Jira and GitHub REST APIs. The challenge was that both APIs return deeply nested JSON — issues with subtasks, comments, transitions, and metadata. I separated the API-fetching code from the transformation logic so the pure functions could be tested without hitting the APIs. The transformation layer would flatten the nested structures, compute metrics like cycle time or PR throughput, and generate Markdown or HTML reports. I also added dry-run planning and collision detection so the automation wouldn't accidentally overwrite existing data."

**Likely follow-ups:**
- How did you handle API rate limits?
- What was the flattening logic like?
- How did collision detection work?

---

### Story 17: STM32 Embedded Validation Tool

**Resume bullet:** "Created UART/I2C validation flow for BME280 sensor checks, firmware-alive confirmation, metadata capture, and per-unit test reports."

**What you actually did:** Built a UART/I2C validation flow for STM32 boards. Verified BME280 sensors, confirmed firmware was alive, captured metadata, generated per-unit test reports.

**10/10 answer:**
"The validation flow was: connect via UART, confirm the firmware was alive with a heartbeat command, switch to I2C to read the BME280 sensor registers — temperature, pressure, humidity — then compare against expected ranges. If everything passed, the script logged the metadata — serial number, firmware version, sensor readings — and generated a per-unit test report. The golden-unit approach helped here too: I'd validate the sensor readings against a known-good unit to set the expected ranges. Any unit outside those ranges flagged for investigation."

**Likely follow-ups:**
- What I2C address did the BME280 use?
- How did you handle sensor initialization timing?
- What were the expected ranges?

---

## PRACTICE SCHEDULE

**Session 1:** Stories 1-3 (16-lane station, golden-unit, communication troubleshooting)
**Session 2:** Stories 4-6 (Python automation, production line, cross-functional)
**Session 3:** Stories 7-10 (Mercury Systems)
**Session 4:** Stories 11-14 (Gatekeeper/Channel Vision)
**Session 5:** Stories 15-17 (Personal projects)

**Before each session:** Read the 10/10 answers aloud 2-3 times.
**During each session:** Record yourself answering. Compare to the 10/10 version.
**After each session:** Note where you drifted — add those to your weak spots list.
