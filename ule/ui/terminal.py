#!/usr/bin/env python3
"""ULE Interactive Terminal UI - Professional Edition."""

import sys
import os
import json
import getpass
import math
from typing import Optional, Dict, List, Any
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from rich.layout import Layout
from rich.live import Live
from rich.status import Status
from datetime import datetime
import hashlib

from ule import connect
from ule.ai import NaturalLanguageQuery

# ============ Professional Terminal UI ============

class ULETerminalUI:
    """Market-standard interactive interface for ULE."""

    def __init__(self, db_path: Optional[str] = None):
        self.console = Console()
        self.db = None
        self.db_path = db_path
        self.running = True
        self.status_msg = "Ready"

    def get_layout(self) -> Layout:
        """Create a professional dashboard layout."""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", minimum_size=20),
            Layout(name="footer", size=3)
        )
        layout["main"].split_row(
            Layout(name="sidebar", size=30),
            Layout(name="body")
        )
        return layout

    def print_header(self):
        """Print application header."""
        header = Text()
        header.append("🌌 ", style="bold")
        header.append("ULE PRO ", style="bold magenta")
        header.append("Universal Ledger Engine", style="bold white")
        header.append(" | ", style="dim")
        header.append("v0.1.0-RC1", style="blue")
        self.console.print(Panel(header, box=box.HORIZONTALS, border_style="magenta"))

    def print_main_dashboard(self):
        """Display the professional main menu."""
        menu_table = Table.grid(padding=1)
        menu_table.add_column(style="cyan bold", justify="right")
        menu_table.add_column(style="white")

        options = [
            ("1", "Open Existing Database"),
            ("N", "Create New Secure Vault"),
            ("2", "SQL relational Console"),
            ("3", "AI Natural Language Query"),
            ("4", "NoSQL Document Store"),
            ("5", "Graph Relationships"),
            ("6", "Vector Similarity Search"),
            ("7", "PQC (Post-Quantum Crypto)"),
            ("8", "Blockchain Audit Trail"),
            ("9", "Engine Statistics"),
            ("Q", "Quantum Simulation"),
            ("0", "Exit System")
        ]

        for code, desc in options:
            menu_table.add_row(f"[{code}]", desc)

        sidebar = Panel(menu_table, title="Navigation", border_style="cyan")
        
        status_color = "green" if self.db else "red"
        conn_text = f"[bold {status_color}]● {self.db_path if self.db else 'Offline'}[/bold {status_color}]"
        
        stats_info = "N/A"
        if self.db:
            try:
                # Count SQL Tables (excluding internal _ ones)
                tables = self.db.execute("SELECT COUNT(*) as count FROM sqlite_master WHERE type='table' AND name NOT LIKE '_%'")[0]['count']
                # Count NoSQL Collections
                colls = self.db.execute("SELECT COUNT(DISTINCT collection) as count FROM _documents")[0]['count']
                stats_info = f"{tables} SQL / {colls} NoSQL"
            except: pass

        info_panel = Panel(
            f"\n  Status:   {conn_text}\n  Database: {stats_info} Active\n  Security: NIST-Lattice Ready\n",
            title="System Info",
            border_style="blue"
        )

        self.console.print(sidebar)
        self.console.print(info_panel)

    def connect(self):
        """Securely connect to a database."""
        path = Prompt.ask("\n[bold]Database Path[/bold]", default="my_vault.udb")
        try:
            # First attempt: Try without password or with empty string
            self.db = connect(path, create_if_missing=True)
            self.db_path = path
            self.status_msg = f"Connected to {path}"
            self.console.print(f"[green]✓ Successfully connected to {path}[/green]")
        except Exception as e:
            error_msg = str(e)
            if "Password required" in error_msg or "encrypted" in error_msg.lower():
                # Secure password prompt
                password = getpass.getpass("🔐 Database is Encrypted. Enter Password: ")
                try:
                    self.db = connect(path, password=password)
                    self.db_path = path
                    self.status_msg = f"Decrypted {path}"
                    self.console.print(f"[green]✓ Vault Decrypted and Connected.[/green]")
                except Exception as e2:
                    self.console.print(f"[red]✗ Access Denied: {e2}[/red]")
            else:
                self.console.print(f"[red]✗ Connection Failed: {e}[/red]")

    def sql_console(self):
        """Interactive SQL terminal."""
        if not self.db:
            self.console.print("[red]✗ error: No active connection. Use Option 1.[/red]")
            return

        self.console.print(Panel(f"[bold yellow]Relational SQL Console[/bold yellow] | [cyan]{self.db_path}[/cyan]\nType 'exit' to return to menu.", border_style="yellow"))
        while True:
            query = Prompt.ask(f"sql@{self.db_path.split('.')[0]}")
            if query.lower() in ("exit", "quit", "0"): break
            try:
                results = self.db.execute(query)
                self.display_results(results)
            except Exception as e:
                self.console.print(f"[red]![/red] {e}")

    def pqc_menu(self):
        """Manage Post-Quantum Cryptography."""
        self.console.print("\n[bold magenta]🛡️ Post-Quantum Security Center[/bold magenta]")
        self.console.print("  [1] Generate New PQC Keypair (ML-KEM/ML-DSA)")
        self.console.print("  [2] Sign Data with ML-DSA")
        self.console.print("  [0] Back")
        
        choice = Prompt.ask("Choice", choices=["0", "1", "2"], default="0")
        
        if choice == "1":
            from ule.engines.pqc_engine import PQCEngine
            pqc = PQCEngine()
            with self.console.status("[bold blue]Generating Lattice Keys..."):
                keys = pqc.generate_kem_keys()
                self.console.print(f"[green]✓ ML-KEM Keys Generated.[/green]")
                self.console.print(f"Public Key: [dim]{keys['public_key'][:50]}...[/dim]")
        elif choice == "2":
            msg = Prompt.ask("Message to sign")
            key = Prompt.ask("Signing Key (JSON)")
            from ule.engines.pqc_engine import PQCEngine
            pqc = PQCEngine()
            sig = pqc.sign(msg, key)
            self.console.print(f"[green]✓ Signature created:[/green] {sig['signature'][:60]}...")

    def display_results(self, results):
        """Display query results in a market-standard table."""
        if not results:
            self.console.print("[yellow]Empty result set.[/yellow]")
            return

        if not isinstance(results, list):
            self.console.print(f"Result: {results}")
            return

        table = Table(box=box.MINIMAL_DOUBLE_HEAD, header_style="bold cyan")
        if results and isinstance(results[0], dict):
            for key in results[0].keys():
                table.add_column(str(key))
            for row in results:
                table.add_row(*[str(v) for v in row.values()])
            self.console.print(table)
        else:
            self.console.print(str(results))

    def create_vault(self):
        """Create a brand new encrypted database."""
        path = Prompt.ask("\n[bold]New Database Name (e.g. project.udb)[/bold]")
        if not path.endswith(".udb"): path += ".udb"
        
        if os.path.exists(path):
            self.console.print(f"[yellow]! File {path} already exists. Use Option 1 to open it.[/yellow]")
            return

        password = getpass.getpass("Set Master Password for this Vault: ")
        confirm = getpass.getpass("Confirm Password: ")
        
        if password != confirm:
            self.console.print("[red]✗ Passwords do not match. Try again.[/red]")
            return

        try:
            with self.console.status("[bold green]Initializing Secure Vault..."):
                # Use the connect helper to init the new DB with password
                from ule.core.connection import connect
                self.db = connect(path, password=password, create_if_missing=True)
                self.db_path = path
                self.status_msg = f"Created {path}"
                self.console.print(f"[green]✓ Success! {path} created and encrypted.[/green]")
        except Exception as e:
            self.console.print(f"[red]✗ Initialization Failed: {e}[/red]")

    def run(self):
        """Main execution loop."""
        os.system('cls' if os.name == 'nt' else 'clear')
        self.print_header()
        
        while self.running:
            self.print_main_dashboard()
            choice = Prompt.ask("\n[bold cyan]Select Action[/bold cyan]", default="0")

            if choice == "1": self.connect()
            elif choice.upper() == "N": self.create_vault()
            elif choice == "2": self.sql_console()
            elif choice == "3": self.nl_query()
            elif choice == "4": self.documents_menu()
            elif choice == "7": self.pqc_menu()
            elif choice == "9": self.show_stats()
            elif choice == "0":
                self.console.print("\n[bold green]System Shutdown. Goodbye.[/bold green]")
                self.running = False
            else:
                self.console.print("[dim]Feature in development for v1.1[/dim]")

    def nl_query(self):
        """AI Natural Language Query Interface."""
        if not self.db:
            self.console.print("[red]✗ Connect to a database first.[/red]")
            return

        self.console.print(Panel("[bold blue]AI Natural Language Engine[/bold blue]\nAsk questions about your data in plain English or Urdu.", border_style="blue"))
        query = Prompt.ask("Question")
        
        with self.console.status("[bold blue]AI is thinking..."):
            try:
                nlq = NaturalLanguageQuery(self.db._conn)
                # Auto-detect or default to English
                results = nlq.ask(query)
                self.display_results(results)
            except Exception as e:
                self.console.print(f"[red]![/red] AI Error: {e}")

    def documents_menu(self):
        """Professional NoSQL Document Manager."""
        if not self.db:
            self.console.print("[red]✗ Connect first.[/red]")
            return

        while True:
            self.console.print(f"\n[bold magenta]📂 NoSQL Document Store[/bold magenta] | [dim]{self.db_path}[/dim]")
            self.console.print("  [1] Push New Document (JSON)")
            self.console.print("  [2] Find/Query Documents")
            self.console.print("  [3] List All Collections")
            self.console.print("  [0] Back")
            
            choice = Prompt.ask("Action", choices=["0", "1", "2", "3"], default="0")
            
            if choice == "1":
                coll = Prompt.ask("Collection", default="default")
                data_str = Prompt.ask("JSON Data", default='{"status": "active"}')
                try:
                    data = json.loads(data_str)
                    doc_id = self.db.push(coll, data)
                    self.console.print(f"[green]✓ Document Saved. ID: {doc_id}[/green]")
                except Exception as e:
                    self.console.print(f"[red]✗ Invalid JSON: {e}[/red]")
            elif choice == "2":
                coll = Prompt.ask("Collection", default="default")
                with self.console.status("[bold magenta]Fetching documents..."):
                    docs = self.db.find(coll)
                    self.display_results(docs)
            elif choice == "3":
                try:
                    res = self.db.execute("SELECT DISTINCT collection FROM _documents")
                    colls = [r['collection'] for r in res]
                    self.console.print(Panel(f"Active Collections:\n[bold cyan]" + "\n".join(colls), title="📂 NoSQL Schema"))
                except Exception as e:
                    self.console.print(f"[red]✗ Error: {e}[/red]")
            else:
                break
    def show_stats(self):
        if self.db: self.console.print(Panel(str(self.db.stats()), title="Database Stats"))
        else: self.console.print("[red]Connect first.[/red]")

def main():
    ui = ULETerminalUI()
    ui.run()

if __name__ == "__main__":
    main()
