from typing import List
from datetime import datetime
from sqlalchemy import text
import classes.HistAlteracoesItemDespesas as HistAlteracoesItemDespesas
import streamlit as st

class HistAlteracoesDespesas:
    nome_tabela = 'hist_alteracoes_despesas'
    def __init__(self, sqlConnSession = None, protocolo = None, nome_arquivo = None, **kwargs):
        self.sqlConnSession = sqlConnSession
        self.id = kwargs.get('id', None)
        self.protocolo = kwargs.get('protocolo', protocolo)
        self.nome_arquivo = kwargs.get('nome_arquivo', nome_arquivo)
        self.id = kwargs.get('id', None)
        self.volume = kwargs.get('volume', None)
        self.qtd_id_osinfo = kwargs.get('qtd_id_osinfo', None)
        self.revertido = kwargs.get('revertido', None)
        self.atributos_normalizados = kwargs.get('atributos_normalizados', None)
        self.created_by = kwargs.get('created_by', None)
        self.created_at = kwargs.get('created_at', datetime.now())
        self.itens = []


    def to_dict(self):
        return {
            "id": self.id,
            "protocolo": self.protocolo,
            "volume": self.volume,
            "nome_arquivo": self.nome_arquivo,
            "qtd_id_osinfo": self.qtd_id_osinfo,
            "revertido": self.revertido,
            "atributos_normalizados": self.atributos_normalizados,
            "created_by": self.created_by,
            "created_at": self.created_at,
        }

    @property
    def id(self): return self._id

    @id.setter
    def id(self, id): self._id = id

    @property
    def volume(self): return self._volume

    @volume.setter
    def volume(self, volume): self._volume = volume

    @property
    def qtd_id_osinfo(self): return self._qtd_id_osinfo

    @qtd_id_osinfo.setter
    def qtd_id_osinfo(self, qtd_id_osinfo): self._qtd_id_osinfo = qtd_id_osinfo

    @property
    def revertido(self): return self._revertido

    @revertido.setter
    def revertido(self, revertido): self._revertido = revertido

    @property
    def atributos_normalizados(self): return self._atributos_normalizados

    @atributos_normalizados.setter
    def atributos_normalizados(self, atributos_normalizados): self._atributos_normalizados = atributos_normalizados

    @property
    def created_by(self): return self._created_by

    @created_by.setter
    def created_by(self, created_by): self._created_by = created_by

    @property
    def created_at(self): return self._created_at

    @created_at.setter
    def created_at(self, created_at): self._created_at = created_at

    @property
    def itens(self): return self._itens

    @itens.setter
    def itens(self, itens): self._itens = itens
        
    @property
    def protocolo(self):
        return self._protocolo
    @protocolo.setter
    def protocolo(self, protocolo):
        if not protocolo or protocolo == "":
            raise ValueError("Protocolo não pode ser vazio")
        self._protocolo = protocolo.strip() 
    
    @property
    def nome_arquivo(self):
        return self._nome_arquivo
    @nome_arquivo.setter
    def nome_arquivo(self, nome_arquivo):
        if not nome_arquivo or nome_arquivo == "":
            raise ValueError("Nome do arquivo não pode ser vazio. (HistAlteracoesDespesas)")
        self._nome_arquivo = nome_arquivo.strip()

    def adicionar_item(self, item: 'HistAlteracoesItemDespesas'):
        item.hist_alteracoes_despesas_id = self.id
        self.itens.append(item)

    def __iter__(self):
        return iter(self.itens)

    def load_from_id(self, id: int):
        with self.sqlConnSession as session:
            query = text("""SELECT * FROM hist_alteracoes_despesas WHERE id = :id""")
            result = session.execute(query, {"id" : id})
            row = result.fetchone()
            if row:
                self.id, self.protocolo, self.volume, self.nome_arquivo, self.qtd_id_osinfo, \
                self.revertido, self.atributos_normalizados, self.created_by, self.created_at = row

    def load_first(self):
        with self.sqlConnSession as session:
            query = text(""" SELECT * FROM hist_alteracoes_despesas 
                                WHERE protocolo = :protocolo
                                AND nome_arquivo = :nome_arquivo
                                AND revertido = 0
                                AND volume = 0 
                          """)
            result = session.execute(query, {"protocolo": self.protocolo, "nome_arquivo": self.nome_arquivo})
            row = result.fetchone()
            if row:
                self.id, self.protocolo, self.volume, self.nome_arquivo, self.qtd_id_osinfo, self.revertido, self.atributos_normalizados, self.created_by, self.created_at = row

    def count_distinct_id_osinfo_itens(self):
        with self.sqlConnSession as session:
            query = text(""" 
                            SELECT
                                COUNT(distinct ITEM.id_despesa_osinfo) AS qtd_item
                            FROM
                                hist_alteracoes_item_despesas AS ITEM
                                JOIN 
                                    (SELECT id FROM hist_alteracoes_despesas 
                                     WHERE protocolo = :protocolo AND nome_arquivo = :nome_arquivo AND revertido = 0
                                    ) AS HISTS ON ITEM.hist_alteracoes_despesas_id = HISTS.id
                     """)
            result = session.execute(query, {"protocolo": self.protocolo, "nome_arquivo": self.nome_arquivo})
            row = result.mappings().fetchone()
            if row:
                return row["qtd_item"]
            
    def get_remaining_items_count(self):
        """
        Retorna a quantidade de linhas que ainda ainda precisam ser processadas (registradas em banco de daodos).
        """
        return (self.qtd_id_osinfo - int(self.count_distinct_id_osinfo_itens()))

    def load_itens(self):
        with self.sqlConnSession as session:
            session.execute("SELECT * FROM hist_alteracoes_item_despesas WHERE hist_alteracoes_despesas_id = %s", (self.id,))
            rows = session.fetchall()
            self.itens = [
                HistAlteracoesItemDespesas(
                    connection=self.connection,
                    id=row["id"],
                    hist_alteracoes_despesas_id=row["hist_alteracoes_despesas_id"],
                    despesa_original=row["despesa_original"],
                    despesa_alterada=row["despesa_alterada"],
                    created_by=row["created_by"],
                    created_at=row["created_at"]
                ) for row in rows
            ]

    def store(self):
        #conn = st.connection('mysql', type='sql')
        with self.sqlConnSession as session:
        #with conn.session as session:
            if self.id:
                query = text("""
                UPDATE hist_alteracoes_despesas
                SET protocolo = :protocolo, volume = :volume, nome_arquivo = :nome_arquivo, qtd_id_osinfo = :qtd_id_osinfo,
                              revertido = :revertido, atributos_normalizados = :atributos_normalizados, created_by = :created_by, created_at = :created_at
                WHERE id = :id
                """)
                result = session.execute(query, 
                            {
                            "protocolo": self.protocolo,
                            "volume": self.volume,
                            "nome_arquivo": self.nome_arquivo,
                            "qtd_id_osinfo": self.qtd_id_osinfo,
                            "revertido": self.revertido or 0,
                            "atributos_normalizados": self.atributos_normalizados or None,
                            "created_by": self.created_by or 1,
                            "created_at": self.created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "id": self.id
                })                    
            else:                             
                query = text("""
                             insert into hist_alteracoes_despesas (protocolo, volume, nome_arquivo, qtd_id_osinfo, revertido, atributos_normalizados, created_by, created_at)
                             values (:protocolo, :volume, :nome_arquivo, :qtd_id_osinfo, :revertido, :atributos_normalizados, :created_by, :created_at)
                             RETURNING id
                             """)
                result = session.execute(query, 
                            {
                            "protocolo": self.protocolo,
                            "volume": self.get_new_volume(),
                            "nome_arquivo": self.nome_arquivo,
                            "qtd_id_osinfo": self.qtd_id_osinfo,
                            "revertido": self.revertido or 0,
                            "atributos_normalizados": self.atributos_normalizados or None,
                            "created_by": self.created_by or 1,
                            "created_at": self.created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                        )
                self.id = result.scalar()
            session.commit()
    def is_duplicate(self):
        with self.sqlConnSession as session:
            query = text(""" SELECT max(volume) as ultimo_volume FROM hist_alteracoes_despesas WHERE protocolo = :protocolo AND nome_arquivo = :nome_arquivo """)
            result = session.execute(query, {"protocolo": self.protocolo, "nome_arquivo": self.nome_arquivo}) 
            row = result.mappings().fetchone()
            return row['ultimo_volume'] is not None

    def get_new_volume(self):
        query = text(""" SELECT COALESCE( (SELECT  MAX(volume) FROM hist_alteracoes_despesas WHERE protocolo = :protocolo AND nome_arquivo = :nome_arquivo AND revertido = 0) + 1, 0) AS volume """)
        return self.sqlConnSession.execute(query, {"protocolo": self.protocolo, "nome_arquivo": self.nome_arquivo}).scalar()

    def is_reverted(self):
        with self.sqlConnSession as session:
            query = text(""" SELECT revertido FROM hist_alteracoes_despesas WHERE 
                         protocolo = :protocolo
                         AND nome_arquivo = :nome_arquivo
                         AND revertido > 0 """)
            result = session.execute(query, {"protocolo": self.protocolo, "nome_arquivo": self.nome_arquivo})
            row = result.fetchone()
            return row is not None

    def store_itens(self):
        for item in self.itens:
            item.store()

    @staticmethod
    def collection_load_by_criteria(connection, criteria: str, fields = 'hist.*') -> list:
        with connection as session:
            query = text(f"SELECT {fields} FROM hist_alteracoes_despesas hist WHERE {criteria}")
            result = session.execute(query) 
            results = result.mappings().fetchall()
        
        registros = []
        for row in results:
            result = HistAlteracoesDespesas(connection, **row)
            registros.append(result)
        return registros