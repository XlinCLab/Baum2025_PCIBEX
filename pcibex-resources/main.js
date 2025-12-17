// Remove PennController command prefix
PennController.ResetPrefix(null);

DebugOff()

SetCounter("counter", "inc", 1); // increment the internal counter


Sequence(
    "consent",
    "demographics",
    "instructions",
    
    // PRACTICE TRIALS
    randomize("practice-trial"),
    "practice-end",

    // BLOCK 1
    rshuffle("1I","1M","1S","1V"),
    //"break",

    // BLOCK 2
    rshuffle("2I","2M","2S","2V"),
    "break",

    // BLOCK 3
    rshuffle("3I","3M","3S","3V"),
    //"break",

    // BLOCK 4
    rshuffle("4I","4M","4S","4V"),
    "break",

    // BLOCK 5
    rshuffle("5I","5M","5S","5V"),
    //"break",

    // BLOCK 6
    rshuffle("6I","6M","6S","6V"),
    "break",

    // BLOCK 7
    rshuffle("7I","7M","7S","7V"),
    "break",

    // BLOCK 8
    rshuffle("8I","8M","8S","8V"),

    SendResults(),
    "end"
);


// Consent form (loaded from html resource)
newTrial("consent",
    newHtml("consent_form", "einverstaendniserklaerung.html")
        .cssContainer({"width":"720px"})
        .checkboxWarning("Sie müssen einwilligen, um fortzufahren.")
        .print()
    ,
    newButton("continue", "Weiter")
        .center()
        .print()
        .wait(getHtml("consent_form").test.complete()
                  .failure(getHtml("consent_form").warn())
        )
)


// Demographics
newTrial("demographics",
     // Automatically print all Text elements, centered
    defaultText
        .center()
        .print()
    ,
    newText("demographics_title", "Demographische Fragen")
        .css("font-size", "2em")
    ,
    newText("required_field_text", "* = Pflichtfeld")
    ,
    newText("\n")
    ,
    // Age / Alter
    newText("age_label", "* Alter:")
        .print()
    ,
    newTextInput("alter", "")
        .center()
        .print()
        .log()
    ,
    newText("\n")
    ,

    // Gender / Geschlecht
    newText("gender_label", "* Geschlecht")
    ,
    newDropDown("geschlecht", "Wählen Sie eine Option aus.")
        .add("Männlich", "Weiblich", "Divers")
        .center()
        .print()
        .log()
    ,
    newText("\n")
    ,
    
    // Muttersprache
    newText("german_native_text", "* Ist Deutsch Ihre Muttersprache?")
    ,
    newDropDown("muttersprache_deutsch", "Wählen Sie eine Option aus.")
        .add("Ja", "Nein")
        .center()
        .print()
        .log()
    ,
    newText("non_german_native_text", "Wenn nicht, was ist Ihre Muttersprache?")
    ,
    newTextInput("andere_muttersprache", "")
        .center()
        .print()
        .log()
    ,
    newText("\n")
    ,
    newText("bilingual_text", "* Gibt es eine oder mehrere weitere Sprache(n), die Sie von Geburt an gelernt haben (d.h. sind Sie bilingual aufgewachsen)?")
    ,
    newDropDown("mehrsprachig", "Wählen Sie eine Option aus.")
        .add("Ja", "Nein")
        .print()
        .center()
        .log()
    ,
    newText("additional_native_langs", "Wenn ja, um welche Sprachen handelt es sich?")
    ,
    newTextInput("weitere_muttersprachen", "")
        .print()
        .center()
        .log()
    ,
    newText("\n")
    ,
    newText("lang_disorder_text", "* Wurde bei Ihnen eine Sprachstörung oder eine Lese-/Rechtschreibschwäche diagnostiziert?")
    ,
    newDropDown("sprachstoerung", "Wählen Sie eine Option aus.")
        .add("Ja", "Nein")
        .center()
        .print()
        .log()
    ,
    newText("\n")
    ,
    newText("germanistik_background_text", "* Studieren Sie aktuell oder haben Sie vorher Germanistik studiert?")
    ,
    newDropDown("germanistik_hintergrund", "Wählen Sie eine Option aus.")
        .add("Ja", "Nein")
        .center()
        .print()
        .log()
    ,

    // Error text placeholder
    newText("error_msg", "")
        .color("red")
        .print()
    ,
    
    newButton("weiter", "Weiter")
        .center()
        .print()
        .wait(
            // Validate that age is a number > 0
            getTextInput("alter").test.text(/^\d+$/)
            
            // Gender required
            .and( getDropDown("geschlecht").test.selected() )
            //getDropDown("geschlecht").test.selected()
    
            // Responses required for other fields
            .and( getDropDown("sprachstoerung").test.selected() )
            .and( getDropDown("germanistik_hintergrund").test.selected() )
            .and( getDropDown("muttersprache_deutsch").test.selected() )
            .and( getDropDown("mehrsprachig").test.selected() )

            // If muttersprache_deutsch == Nein, andere_muttersprache response required
            .and(
                getDropDown("muttersprache_deutsch").test.selected("Ja")
                .or(
                    getTextInput("andere_muttersprache").testNot.text("")
                )
            )

            // If mehrsprachig == Ja, weitere_muttersprachen response required
            .and(
                getDropDown("mehrsprachig").test.selected("Nein")
                .or(
                    getTextInput("weitere_muttersprachen").testNot.text("")
                )
            )
    
            // Error message on field validation failure
            .failure(
                getText("error_msg")
                    .text("Bitte füllen Sie alle erforderlichen Felder korrekt aus.")
            )
        )
    )
;


// Instructions
newTrial("instructions",
    newHtml("instruction_form", "anleitung.html")
        .cssContainer({"width":"720px"})
        .print()
    ,
    newButton("continue", "Weiter")
        .center()
        .print()
        .wait(getHtml("instruction_form").test.complete()
                  .failure(getHtml("instruction_form").warn())
        )
)


// Practice trials
Template("practice-stimuli.csv", row =>
    newTrial("practice-trial",
        defaultText
            .css("font-size", "1.5em")
            .center()
        ,
        newButton("Weiter")
            .css("font-size", "1.5em")
            .center()
            .print()
            .wait()
            .remove()
        ,
        newController(
            "DashedSentence_pt1",
            "DashedSentence",
            { s: row.stimulussatz
                .split("//")[0]                     // split component sentences and extract first sentence
                .split("/")                         // split into chunks by "/" delimiter
                .map(w => w.replace(/\*/g, ""))     // remove all asterisks
            }
        )
            .css("font-size", "1.5em")
            .css("white-space","nowrap")
            .center()
            .print()
            .log()
            .wait()
        ,
        newController(
            "DashedSentence_pt2",
            "DashedSentence",
            { s: row.stimulussatz
                .split("//")[1]                     // split component sentences and extract second sentence
                .split("/")                         // split into chunks by "/" delimiter
                .map(w => w.replace(/\*/g, ""))     // remove all asterisks
            }
        )
            .css("font-size", "1.5em")
            .css("white-space","nowrap")
            .center()
            .print()
            .log()
            .wait()
        ,
        getController("DashedSentence_pt1")
            .remove()
        ,
        getController("DashedSentence_pt2")
            .remove()
        ,
        // Comprehension question, if available for this item
        ...(row.verstaendnisfrage && row.verstaendnisfrage.trim() !== "" ? [
            newText(row.verstaendnisfrage)
                .print()
            ,
            newButton("ja", "Ja")
                .css("font-size", "1.5em")
                .remove()
            ,
            newButton("nein", "Nein")
                .css("font-size", "1.5em")
                .remove()
            ,
            newCanvas("yes-no-responses", 450,200)
                .add(100, 0, getButton("ja"))
                .add(300, 0, getButton("nein"))
                .center()
                .print()
                .log()
            ,
            newSelector("selection")
                .add(getButton("ja"), getButton("nein"))
                //.shuffle()
                .wait()
                .log()
            ,
        ] : [])
        )
        .log("uebung", "TRUE")
        .log("itemNummer", row.itemNummer)
        .log("kontext", row.kontext)
        .log("bedingung", row.bedingung)
        .log("anapherArt", row.anapherArt)
        .log("unterkategorie", row.unterkategorie)
        .log("spezifikation", row.spezifikation)
        .log("anker", row.anker)
        .log("anapher", row.anapher)
        .log("anapherIdx", row.anapherIdx)
        .log("verstaendnisfrage", row.verstaendnisfrage)
        .log("erwarteteAntwort", row.erwarteteAntwort)
)


// Announce end of practice trials and start of real experimental trials
newTrial("practice-end",
    newText("Nun haben Sie die Aufgabe geübt.\n\nKlicken  Sie, um das Experiment zu starten.")
        .css("font-size", "1.5em")
        .center()
        .print()
    ,
    newButton("Weiter")
        .css("font-size", "1.5em")
        .center()
        .print()
        .wait()
        .remove()
)


// Main experimental trials
Template("blocked_trials.csv", row => 
    newTrial(row.block_bedingung,
        defaultText
            .css("font-size", "1.5em")
            .center()
        ,
        newButton("Weiter")
            .css("font-size", "1.5em")
            .center()
            .print()
            .wait()
            .remove()
        ,
        newController(
            "DashedSentence_pt1",
            "DashedSentence",
            { s: row.stimulussatz
                .split("//")[0]                     // split component sentences and extract first sentence
                .split("/")                         // split into chunks by "/" delimiter
                .map(w => w.replace(/\*/g, ""))     // remove all asterisks
            }
        )
            .css("font-size", "1.5em")
            .css("white-space","nowrap")
            .center()
            .print()
            .log()
            .wait()
        ,
        newController(
            "DashedSentence_pt2",
            "DashedSentence",
            { s: row.stimulussatz
                .split("//")[1]                     // split component sentences and extract second sentence
                .split("/")                         // split into chunks by "/" delimiter
                .map(w => w.replace(/\*/g, ""))     // remove all asterisks
            }
        )
            .css("font-size", "1.5em")
            .css("white-space","nowrap")
            .center()
            .print()
            .log()
            .wait()
        ,
        getController("DashedSentence_pt1")
            .remove()
        ,
        getController("DashedSentence_pt2")
            .remove()
        ,
        // Comprehension question, if available for this item
        ...(row.verstaendnisfrage && row.verstaendnisfrage.trim() !== "" ? [
            newText(row.verstaendnisfrage)
                .print()
            ,
            newButton("ja", "Ja")
                .css("font-size", "1.5em")
                .remove()
            ,
            newButton("nein", "Nein")
                .css("font-size", "1.5em")
                .remove()
            ,
            newCanvas("yes-no-responses", 450,200)
                .add(100, 0, getButton("ja"))
                .add(300, 0, getButton("nein"))
                .center()
                .print()
                .log()
            ,
            newVar("QuestionStartTime")
                .set( v => Date.now() )
                .log()
            ,
            newSelector("selection")
                .add(getButton("ja"), getButton("nein"))
                //.shuffle()
                .wait()
                .log()
            ,
            newVar("QuestionEndTime")
                .set( v => Date.now() )
                .log()
        ] : [])
        )
        .log("uebung", "FALSE")
        .log("itemNummer", row.itemNummer)
        .log("block", row.block)
        .log("kontext", row.kontext)
        .log("bedingung", row.bedingung)
        .log("anapherArt", row.anapherArt)
        .log("unterkategorie", row.unterkategorie)
        .log("spezifikation", row.spezifikation)
        .log("anker", row.anker)
        .log("anapher", row.anapher)
        .log("anapherIdx", row.anapherIdx)
        .log("verstaendnisfrage", row.verstaendnisfrage)
        .log("erwarteteAntwort", row.erwarteteAntwort)
)


// Break/pause between trials
newTrial("break",
    defaultText
        .css("font-size", "1.5em")
        .center()
        .print()
    ,
    newText("break-announcement", "Bitte nehmen Sie eine kurze Pause, bevor es weitergeht.")
    ,
    newVar("BreakStartTime")
        .set( v => Date.now() )
        .log()
    ,
    newTimer("wait", 30000) // wait 30 seconds before displaying button to continue
        .start()
        .wait()
    ,
    getText("break-announcement")
        .remove()
    ,
    newText("Klicken Sie, um das Experiment fortzusetzen.")
    ,
    newButton("Weiter")
        .center()
        .css("font-size", "1.5em")
        .print()
        .wait()
        .remove()
    ,
    newVar("BreakEndTime")
        .set( v => Date.now() )
        .log()
)


// Final screen
newTrial("end",
    defaultText
        .css("font-size", "1.5em")
        .center()
        .print()
    ,
    newText("Vielen Dank für Ihre Teilnahme!")
    ,
    // Trick: stay on this trial forever (until tab is closed)
    newButton().wait()
)
.setOption("countsForProgressBar",false)