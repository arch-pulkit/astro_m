/*
Remaking app.py with GoLang

Keeping same API as the FastAPI version
*/

// Every Go file starts with packaage name; and
// main means execution starts at func main()
package main

import (
	"database/sql"
	"encoding/json"
	"errors"
	"log"
	"net/http"
	"os"
	"strings"

	//same as python dotenv
	"github.com/joho/godotenv"
	// '_' means import for its side effect only, we import sql but never use it
	_ "modernc.org/sqlite"
)


//Go JSON decoder does NOT validate as Pydantic does,
// so if a field is missing it silently becomes "" rather than error

// For pydantics behavior exactly, we use *string (a pointer to a string)
// Pointer can be nil 

// `json: "..."` are struct tags, they tell JSON decoder whcih JSON key maps to which Go field
// Go field must start with a Capital Letter to be visible 

type recordInput struct {
	Prompt    *string `json:"prompt"`
	Response  *string `json:"response"`
	Timestamp *string `json:"timestamp"`
	ModelName *string `json:"model_name"`

}


// Record is the clean version we work with

type Record struct {
	Prompt    string `json:"prompt"`
	Response  string `json:"response"`
	Timestamp string `json:"timestamp"`
	ModelName string `json:"model_name"`
}

//it is Record plus its database id
// writing `Record` with no field name is called "embeding"
//all of Record's fields get prompted into StoreRecord to match flat rows which Py GET endpoint returned.

type StoreRecord struct {
	ID int64 `json:"id"`
	Record
}

// method on recordInput
// (in recordInput) part before functions name is "receiver", Go's `self`
//Go has no exceptions, so if fail it returns an extra error value
// Returning (Record, error) is same ass Pydantic raising ValidationError

func (in recordInput) toRecord() (Record, error) {
	var missing []string // called slice, Go's list

	if in.Prompt == nil {
		missing = append(missing, "prompt")
	}
	if in.Response == nil {
		missing = append(missing, "response")
	}
	if in.Timestamp == nil {
		missing = append(missing, "timestamp")
	}
	if in.ModelName == nil {
		missing = append(missing, "model_name")
	}

	//When an error callers are expected to ignore other value, hence empty record
	if len(missing) > 0 {
		return Record{}, errors.New("missing required field(s): " + strings.Join(missing, ", "))
	}

	// *in.--- deferences the pointer, its gets the string it points to
	return Record {
		Prompt: *in.Prompt,
		Response: *in.Response,
		Timestamp: *in.Response,
		ModelName: *in.ModelName,
	}, nil //for no errors
}

/*
Database Setup 

Almost same, difference is that Py defauled database.db next to app.py
Go binary can be run from anywhere, so we dafault it in current working directory isntead
*/

func dbPathFromEnv() string {
	url := os.Getenv("ASTRO_DB_PATH")
	if url == ""{
		return "database.db"
	}
	return strings.TrimPrefix(url, "sqlite:///")
}


func initDB(db *sql.DB) error {
	// Backticks make a raw multi-line string, like Py's triple quotes
	_, err := db.Exec(`
	CREATE TABLE IF NOT EXISTS records (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		prompt TEXT,
		response TEXT, 
		timestamp TEXT, 
		model_name TEXT	
	)`)
//db.Exec returns (result, error). We dont need the result, so we assign to it _
//Go refuses to compile if you leave a variable unused
	return err
}

/*
Servers
In py, every endpoiint called sqlite3.connect() and closed it at end.
In Go, *sql.DB is a connection POOL, open it once at startup and share it across all requests.
*/

type server struct {
	db *sql.DB
}

// writeJSON sends any Go value as JSON response
// `any` means a value of any typpe
func writeJSON(w http.ResponseWriter, status int, v any) {
	//Headers must eb set before WriteHeader, sends the status line
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)

	//Encode turns v into JSON and writes it straight into response
	if err := json.NewEncoder (w).Encode(v); err != nil {
		log.Printf("writing response failed: %v", err)
	}
}

// writeError is like FastAPI's HTTPException response share
func writeError (w http.ResponseWriter, status int, msg string) {
	writeJSON(w, status, map[string]string{"detail": msg})
}

/*
Handlers @app.get/post functions

w http.ResponseWriter -> where we write the response
r *http.Request       -> the incoming request (body, headers, URL ...)

No return value, we write to w and return
*/


// health: GET /
func (s *server) health(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusOK, map[string]string{"Status": "OK"})
}


// POST /records
func (s *server) createRecord(w http.ResponseWriter, r *http.Request) {
	//capping body at 10MB so no endless req
	// in GO we have to add protection
	// 10 << 20 = 10 * 1024 * 1024
	r.Body = http.MaxBytesReader(w, r.Body, 10 << 20)

	// 1. Decode JSOn into pointer struct
	// We pass &in (its address) so Decode can fill it in

	var in recordInput
	if err := json.NewDecoder(r.Body).Decode(&in); err != nil {
		//covers broken JSON; FastAPI returned 422 fot these
		writeError(w, http.StatusUnprocessableEntity, "invalid JSON: "+err.Error())

		return //in GO, must return after an error
	}

	// 2. validate (Pydantic did it automatically)
	rec, err := in.toRecord()
	if err != nil {
		writeError(w, http.StatusUnprocessableEntity, err.Error())
		return
	}

	// 3. insert. '?' placeholders same as PY
	//sqlite3 values are sent as data, never pasted into SQL text, so SQL injection safe

	//if client disconnets mid-req, context is cancelled and query can stop early
	result, err := s.db.ExecContext(r.Context(),
		`INSERT INTO records (prompt, response, timestamp, model_name)
		VALUES (?, ?, ?, ?)`,
		rec.Prompt, rec.Response, rec.Timestamp, rec.ModelName, 
	)
	if err != nil {
		//log real error later
		log.Printf("insert failed: %v", err)
		writeError(w, http.StatusInternalServerError, "failed to save record")
		return
	}

	//cursor.lastrowid Py
	newID, err := result.LastInsertId()
	if err != nil {
		log.Printf("reading new id failed: %v", err)
		writeError(w, http.StatusInternalServerError, "Failed to save record")
		return
	}

	//map[string]any let us build a dict on the fly
	writeJSON(w, http.StatusOK, map[string]any {
		"id": newID,
		"data": rec,
	})
}

// GET /records
func (s *server) listRecords(w http.ResponseWriter, r*http.Request) {
	// instead of SELECT *, we list columns explicitly, it gurantee the order
	rows, err := s.db.QueryContext(r.Context(),
		`SELECT id, prompt, response, timestamp, model_name FROM records`)
	if err != nil {
		log.Printf("select failed: %v", err)
		writeError(w, http.StatusInternalServerError, "Failed to load records")
		return
	}

	// GO's version of finally: conn.close()
	//forgetting to close leaks a connection from the pool
	defer rows.Close()

	//Start with an empty slice, a nil slice encodes JSON as null an empty one as []
	records := []StoreRecord{}

	//replaces Py's fetchall() + row_factory
	for rows.Next() {
		var rec StoreRecord
		if err := rows.Scan(&rec.ID, &rec.Prompt, &rec.Response, &rec.Timestamp, &rec.ModelName); err != nil {
			log.Printf("scan failed: %v", err)
			writeError(w, http.StatusInternalServerError, "Failed to load records")
			return
		}
		records = append(records, rec)
	}

	//tells which error happend for loop to be closed
	if err := rows.Err(); err != nil {
		log.Printf("row iteration failed: %v", err)
		writeError(w, http.StatusInternalServerError, "Failed to load records")
		return
	}
	writeJSON(w, http.StatusOK, records)
}


// DELETE /records/clear
func (s *server) clearrRecords(w http.ResponseWriter, r *http.Request) {

	tx, err := s.db.BeginTx(r.Context(), nil)
	if err != nil {
		log.Printf("begin tx failed: %v", err)
		writeError(w, http.StatusInternalServerError, "Failed to clear records")
		return
	}

	//if anything below returns early, Rollback undoes the partial work
	defer tx.Rollback()

	if _, err := tx.ExecContext(r.Context(), `DELETE FROM records`); err != nil {
		log.Printf("delete failed: %v", err)
		writeError(w, http.StatusInternalServerError, "Failed to clear records")
		return
	}

	//RESET autoincrement for ids
	if _, err := tx.ExecContext(r.Context(),
		`DELETE FROM sqlite_sequence WHERE name = 'records`); err != nil {
			log.Printf("reset sequence failed: %v", err)
			writeError(w, http.StatusInternalServerError, "Failed to clear records")
			return
		}
	if err := tx.Commit(); err != nil {
		log.Printf("commit failed: %v", err)
		writeError(w, http.StatusInternalServerError, "Failed to clear recods")
		return
	}
	writeJSON(w, http.StatusOK, map[string]string{"message": "data cleared"})
}

// lifespan function + uvicorn command together in main

func main() {
	//returns an error if no .env file, hence the '_' to ignore it
	_ = godotenv.Load()

	path := dbPathFromEnv()

	//sql.Open does not connect yet, only cheks the arguments and prepares the pool
	db, err := sql.Open("sqlite", path)

	if err != nil {
		// log.Fatal prints and exits
		log.Fatalf("opening database: %v", err)
	}
	defer db.Close() //closes pool when main returns

	//SQLite allows only one writer at a time, so limititng pool to 1 connection
	//makes requests take turns instead.

	db.SetMaxOpenConns(1)

	//like lifespan(), set up the table before serving requests
	if err := initDB(db); err != nil {
		log.Fatalf("initializing database: %v", err)
	}
	
	//& gives a pointer, so all handlers share one server
	s := &server{db: db}

	//Go's builtin router like FastAPI

	mux := http.NewServeMux()

	// "GET /" in Go matches EVERY path, {$} means exactly nothing after it
	mux.HandleFunc("GET /{$}", s.health)
	mux.HandleFunc("POST /records", s.createRecord)
	mux.HandleFunc("GET /records", s.listRecords)
	mux.HandleFunc("DELETE /records/clear", s.clearrRecords)

	//railway sets port, locally we fall back to 8000, uvicrons default
	port := os.Getenv("PORT")
	if port == ""{
		port = "8000"
	}
	log.Printf("ASTR-O listening on :%s (db: %s)", port, path)

	//ListenandServe blocks forever and handles each request in its own goroutine

	if err := http.ListenAndServe(":"+port, mux); err != nil {
		log.Fatalf("server stopped: %v", err)
	}
}



